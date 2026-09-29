"""Audit, export and apply existing NSI profile requirements to a separate MIS database."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
from firebird.driver import (
    Connection, Cursor, DefaultAction, Isolation, TableAccessMode, TableShareMode,
    TPB, connect, driver_config,
)
from firebird.driver.core import TransactionManager


PROFILE_NAME_LIMIT = 200  # SYNC_PROFILE.SYNCPROFNAME is VARCHAR(200) in the MIS


def profile_name(code: str, semd_name: str) -> str:
    """Name shown in the loader manager: the kind code first, then its full title.

    Titles of 20 kinds are longer than the column allows; the tail is cut and the full
    title stays in the profile comment, so the code prefix is what identifies the set.
    """
    name = f"СЭМД {code} {semd_name}"
    if len(name) > PROFILE_NAME_LIMIT:
        return name[: PROFILE_NAME_LIMIT - 1] + "…"
    return name


def rows(cursor: Cursor, sql: str) -> list[dict[str, Any]]:
    cursor.execute(sql)
    names = [column[0].lower() for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def read_catalog(dsn: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    connection = psycopg2.connect(dsn)
    try:
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM public.rpt_semd_guides ORDER BY semd_code")
            guides = [dict(row) for row in cursor.fetchall()]
            cursor.execute("""
                SELECT r.semd_code, r.dict_oid, r.dict_name, r.dict_version,
                       r.dict_id_field, g.raw_json -> 'COLLECTION' AS collection
                FROM public.rpt_semd_dictionaries r
                JOIN public.dim_nsi_semd_guide_dictionary g
                  ON g.guide_oid = r.guide_oid AND g.dict_oid = r.dict_oid
                ORDER BY r.semd_code, r.dict_oid
            """)
            pairs = [dict(row) for row in cursor.fetchall()]
            cursor.execute("""
                SELECT source_oid, source_version, count(*) AS records, max(loaded_at) AS loaded_at
                FROM public.dim_nsi_semd_guide GROUP BY 1, 2
                UNION ALL
                SELECT source_oid, source_version, count(*), max(loaded_at)
                FROM public.dim_nsi_semd_guide_dictionary GROUP BY 1, 2
            """)
            sources = [dict(row) for row in cursor.fetchall()]
        return guides, pairs, sources
    finally:
        connection.rollback()
        connection.close()


def classify(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "missing"
    if len(matches) != 1:
        return "ambiguous"
    reference = matches[0]
    if reference["disabled"] not in (None, 0):
        return "disabled"
    if reference["grouptype"] not in (None, 0):
        return "group"
    return "matched" if reference["reftype"] == 1 else "wrong_source"


def audit(connection: Connection, dsn: str) -> dict[str, Any]:
    guides, pairs, sources = read_catalog(dsn)
    cursor = connection.cursor()
    identity = rows(cursor, """
        SELECT rdb$get_context('SYSTEM', 'DB_NAME') AS db_path,
               rdb$get_context('SYSTEM', 'ENGINE_VERSION') AS engine
        FROM rdb$database
    """)[0]
    references = rows(cursor, """
        SELECT syncrefid, refcode, refname, reftype, grouptype, disabled,
               reftable, refhandler, syncverid FROM sync_reference ORDER BY syncrefid
    """)
    by_oid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for reference in references:
        by_oid[reference["refcode"]].append(reference)
    dictionaries: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        oid = pair["dict_oid"]
        dictionaries[oid] = {
            "dict_name": pair.pop("dict_name"),
            "status": classify(by_oid[oid]),
            "matches": by_oid[oid],
        }
    coverage: Counter[str] = Counter()
    profile_coverage: dict[str, Counter[str]] = defaultdict(Counter)
    for pair in pairs:
        status = dictionaries[pair["dict_oid"]]["status"]
        coverage[status] += 1
        profile_coverage[pair["semd_code"]][status] += 1
    connection.rollback()
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "firebird": identity,
        "sources": sources,
        "guides": guides,
        "pairs": pairs,
        "dictionaries": dictionaries,
        "coverage": dict(coverage),
        "oid_coverage": dict(Counter(item["status"] for item in dictionaries.values())),
        "profile_coverage": {key: dict(value) for key, value in profile_coverage.items()},
    }


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def seed_sql(report: dict[str, Any], code: str, uid: int | None, filial: int | None,
             *, partial: bool, verification: bool = False, fail_on_conflict: bool = False,
             current_database: bool = False) -> str:
    if not re.fullmatch(r"[0-9]+", code):
        raise ValueError("The selected semd_code must be numeric")
    guide = next(item for item in report["guides"] if item["semd_code"] == code)
    pairs = [item for item in report["pairs"] if item["semd_code"] == code]
    oids = sorted({item["dict_oid"] for item in pairs})
    if not oids or len(oids) != len(pairs):
        raise ValueError("Missing or duplicated source dictionary requirements")
    if any(not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", oid) for oid in oids):
        raise ValueError("Invalid dictionary OID")
    if not guide["semd_is_cda"]:
        raise ValueError("The selected guide is not a CDA document type")
    actor_uid = str(uid) if uid is not None else "CAST(RDB$GET_CONTEXT('USER_SESSION', 'SYNC_PROFILE_UID') AS BIGINT)"
    actor_filial = str(filial) if filial is not None else "CAST(RDB$GET_CONTEXT('USER_SESSION', 'SYNC_PROFILE_FILIAL') AS INTEGER)"
    actor_columns = "" if current_database else ", filial, uid"
    actor_values = "" if current_database else f", {actor_filial}, {actor_uid}"
    actor_update = "" if current_database else f"uid = {actor_uid}, "
    actor_check = "" if current_database else f"""
    IF (NOT EXISTS(SELECT 1 FROM doctor WHERE dcode = {actor_uid}) OR
        NOT EXISTS(SELECT 1 FROM filials WHERE filid = {actor_filial})) THEN
    BEGIN
        status = 'INVALID_ACTOR'; SUSPEND; EXIT;
    END
"""
    end_date = f"DATE {literal(str(guide['semd_end_date']))}" if guide["semd_end_date"] else "NULL"
    name = profile_name(code, guide["semd_name"])
    legacy_name = f"СЭМД {code}"
    source_versions = "; ".join(
        f"{item['source_oid']}/{item['source_version']}" for item in report["sources"]
    )
    comment = (
        f"{guide['semd_name']}. Руководство {guide['guide_oid']}; редакция {guide['guide_release']}. "
        f"Источник: rpt_semd_dictionaries; НСИ {source_versions}. Требуется {len(oids)} OID. "
        + ("Проверка записи с последующим откатом. " if verification else "")
        + "Версии и ограничения значений проверяются отдельно. Сопоставлено "
    )
    if len(comment) > 950:
        raise ValueError("Profile comment exceeds the target domain capacity")
    expected = ",\n            ".join(literal(oid) for oid in oids)
    eligible = f"""
        SELECT r.syncrefid
        FROM sync_reference r
        WHERE r.refcode IN ({expected})
          AND COALESCE(r.disabled, 0) = 0 AND COALESCE(r.grouptype, 0) = 0
          AND r.reftype = 1
          AND (SELECT COUNT(*) FROM sync_reference x WHERE x.refcode = r.refcode) = 1
    """
    return f"""EXECUTE BLOCK RETURNS (
    status VARCHAR(64), profile_id BIGINT, mapped_count INTEGER,
    missing_count INTEGER, created_profile INTEGER, updated_profile INTEGER,
    inserted_links INTEGER, extra_links INTEGER
)
AS
DECLARE VARIABLE candidate_count INTEGER;
DECLARE VARIABLE reference_id BIGINT;
DECLARE VARIABLE profile_comment VARCHAR(1024);
BEGIN
    created_profile = 0;
    updated_profile = 0;
    inserted_links = 0;
    SELECT COUNT(*) FROM ({eligible}) INTO :mapped_count;
    missing_count = {len(oids)} - mapped_count;
    profile_comment = {literal(comment)} || CAST(mapped_count AS VARCHAR(12)) ||
        ' из {len(oids)}; отсутствует ' || CAST(missing_count AS VARCHAR(12)) || '.';
    IF (missing_count > 0 AND {int(partial)} = 0) THEN
    BEGIN
        status = 'INCOMPLETE'; SUSPEND; EXIT;
    END
    IF (mapped_count = 0) THEN
    BEGIN
        status = 'NO_AVAILABLE_REFERENCES'; SUSPEND; EXIT;
    END
    {actor_check}
    SELECT COUNT(*), MIN(syncprofid) FROM sync_profile
    WHERE syncprofident = {literal(code)} OR
        (NULLIF(TRIM(syncprofident), '') IS NULL
         AND syncprofname IN ({literal(legacy_name)}, {literal(name)}))
    INTO :candidate_count, :profile_id;
    IF (candidate_count > 1) THEN
    BEGIN
        status = 'AMBIGUOUS_PROFILE'; SUSPEND; EXIT;
    END
    IF (EXISTS(SELECT 1 FROM sync_profile WHERE syncprofid = {code}
               AND syncprofid IS DISTINCT FROM :profile_id)) THEN
    BEGIN
        status = 'CODE_ID_COLLISION'; SUSPEND; EXIT;
    END
    IF (EXISTS(SELECT 1 FROM sync_profile WHERE syncprofid = :profile_id
               AND ((fdate IS NOT NULL AND fdate IS DISTINCT FROM {end_date})
                    OR NULLIF(TRIM(syncprof_sp), '') IS NOT NULL))) THEN
    BEGIN
        status = 'PROFILE_REQUIRES_REVIEW'; SUSPEND; EXIT;
    END
    IF (EXISTS(SELECT 1 FROM sync_profile_links WHERE syncprofid = :profile_id
              GROUP BY syncrefid HAVING COUNT(*) > 1)) THEN
    BEGIN
        status = 'DUPLICATE_LINKS'; SUSPEND; EXIT;
    END
    IF (candidate_count = 0) THEN
    BEGIN
        profile_id = GEN_ID(sync_profile_gen, 1);
        INSERT INTO sync_profile
            (syncprofid, parent_syncprofid, syncprofname, syncprofident, comment,
             fdate{actor_columns}, modifydate)
        VALUES (:profile_id, 0, {literal(name)}, {literal(code)}, :profile_comment,
                {end_date}{actor_values}, CURRENT_TIMESTAMP);
        created_profile = 1;
    END
    ELSE IF (EXISTS(SELECT 1 FROM sync_profile WHERE syncprofid = :profile_id
              AND (syncprofident IS DISTINCT FROM {literal(code)}
                   OR syncprofname IS DISTINCT FROM {literal(name)}
                   OR comment IS DISTINCT FROM :profile_comment
                   OR fdate IS DISTINCT FROM {end_date}))) THEN
    BEGIN
        UPDATE sync_profile SET syncprofident = {literal(code)}, syncprofname = {literal(name)},
            comment = :profile_comment,
            fdate = {end_date}, {actor_update}modifydate = CURRENT_TIMESTAMP WHERE syncprofid = :profile_id;
        updated_profile = 1;
    END
    FOR {eligible} INTO :reference_id DO
    BEGIN
        IF (NOT EXISTS(SELECT 1 FROM sync_profile_links
                       WHERE syncprofid = :profile_id AND syncrefid = :reference_id)) THEN
        BEGIN
            INSERT INTO sync_profile_links
                (syncproflinkid, syncprofid, syncrefid{actor_columns}, modifydate)
            VALUES (GEN_ID(sync_profile_links_gen, 1), :profile_id, :reference_id{actor_values}, CURRENT_TIMESTAMP);
            inserted_links = inserted_links + 1;
        END
    END
    SELECT COUNT(*) FROM sync_profile_links l
    WHERE l.syncprofid = :profile_id AND NOT EXISTS (
        SELECT 1 FROM ({eligible}) e WHERE e.syncrefid = l.syncrefid
    ) INTO :extra_links;
    status = IIF(missing_count = 0, 'COMPLETE', '{'PARTIAL_VERIFICATION' if verification else 'PARTIAL_SOURCE'}');
    SUSPEND;
END
""".replace("SUSPEND; EXIT;", "EXCEPTION ERROR status;" if fail_on_conflict else "SUSPEND; EXIT;")


def snapshot(cursor: Cursor) -> dict[str, Any]:
    return {
        "profiles": rows(cursor, "SELECT * FROM sync_profile ORDER BY syncprofid"),
        "links": rows(cursor, "SELECT * FROM sync_profile_links ORDER BY syncproflinkid"),
    }


def catalog_codes(report: dict[str, Any]) -> list[str]:
    return sorted(report["profile_coverage"], key=int)


def protected_transaction(connection: Connection) -> TransactionManager:
    policy = TPB(isolation=Isolation.SNAPSHOT, lock_timeout=10)
    for table in ("SYNC_PROFILE", "SYNC_PROFILE_LINKS"):
        policy.reserve_table(table, TableShareMode.PROTECTED, TableAccessMode.LOCK_WRITE)
    manager = connection.transaction_manager(policy.get_buffer(), DefaultAction.ROLLBACK)
    manager.begin()
    return manager


def export_sql(report: dict[str, Any], output: Path) -> Path:
    statements = [seed_sql(report, code, None, None, partial=True, fail_on_conflict=True,
                           current_database=True)
                  for code in catalog_codes(report)]
    header = """-- Execute in the current Firebird database, using a dedicated UTF8 connection.
-- No connection switching or external databases. No user or branch parameters.
-- Keep native defaults and replication triggers; preserve existing UID and FILIAL.
SET BAIL ON;
SET AUTODDL OFF;
COMMIT;
SET TRANSACTION READ WRITE WAIT ISOLATION LEVEL SNAPSHOT
    RESERVING SYNC_PROFILE, SYNC_PROFILE_LINKS FOR PROTECTED WRITE;
SET TERM ^ ;
"""
    path = output / "sync_profiles_load.sql"
    path.write_text(header + "\n^\n".join(statements) + "\n^\nCOMMIT^\nSET TERM ; ^\n",
                    encoding="utf-8")
    export_editor_sql(statements, output)
    return path


def export_editor_sql(statements: list[str], output: Path) -> Path:
    blocks: list[str] = []
    for statement in statements:
        signature, body = statement.split("\nAS\n", 1)
        fields = signature.removeprefix("EXECUTE BLOCK RETURNS (\n").rstrip().removesuffix(")")
        declarations = "\n".join(f"DECLARE VARIABLE {field.strip()};" for field in fields.split(","))
        body = body.replace("    SUSPEND;\n", "")
        if "SUSPEND" in body:
            raise ValueError("Editor block must not return a result set")
        blocks.append("EXECUTE BLOCK AS\n" + declarations + "\n" + body.strip() + ";")
    path = output / "sync_profiles_firebird.sql"
    path.write_text("-- Firebird PSQL for the current database. Execute in script mode.\n"
                    "-- The SQL client owns the transaction; this file does not commit.\n"
                    + "\n\n".join(blocks) + "\n", encoding="utf-8")
    return path


def apply_catalog(connection: Connection, report: dict[str, Any], uid: int,
                  filial: int, output: Path) -> dict[str, Any]:
    before = snapshot(connection.cursor())
    connection.rollback()
    write_json(output / "before-import.json", before)
    passes: list[dict[str, Any]] = []
    first_state: dict[str, Any] | None = None
    first_generators: list[dict[str, Any]] | None = None
    for pass_number in (1, 2):
        manager = protected_transaction(connection)
        cursor = manager.cursor()
        results: list[dict[str, Any]] = []
        try:
            for key, value in (("SYNC_PROFILE_UID", uid), ("SYNC_PROFILE_FILIAL", filial)):
                cursor.execute("SELECT rdb$set_context('USER_SESSION', ?, ?) FROM rdb$database",
                               (key, str(value)))
                cursor.fetchone()
            for index, code in enumerate(catalog_codes(report), 1):
                result = rows(cursor, seed_sql(report, code, None, None,
                                              partial=True, fail_on_conflict=True))[0]
                if result["status"] not in ("COMPLETE", "PARTIAL_SOURCE"):
                    raise RuntimeError(f"Profile {code}: {result['status']}")
                result["semd_code"] = code
                results.append(result)
                if index % 50 == 0:
                    print(f"Pass {pass_number}: {index} profiles checked", flush=True)
            state = snapshot(cursor)
            current_generators = generators(cursor)
            duplicates = rows(cursor, """
                SELECT syncprofid, syncrefid, COUNT(*) AS copies FROM sync_profile_links
                GROUP BY syncprofid, syncrefid HAVING COUNT(*) > 1
            """)
            if duplicates:
                raise RuntimeError("Duplicate profile links")
            if pass_number == 1:
                first_state, first_generators = state, current_generators
            elif state != first_state or current_generators != first_generators:
                raise RuntimeError("Second transaction changed rows or generators")
            totals = {key: sum(row[key] for row in results)
                      for key in ("created_profile", "updated_profile", "inserted_links")}
            passes.append({"pass": pass_number, "totals": totals, "profiles": results,
                           "generators": current_generators})
            manager.commit()
            write_json(output / f"import-pass-{pass_number}.json", passes[-1])
        finally:
            if manager.is_active():
                manager.rollback()
            manager.close()
    after = snapshot(connection.cursor())
    connection.rollback()
    write_json(output / "after-import.json", after)
    return {"committed": True, "profiles": len(after["profiles"]), "links": len(after["links"]),
            "repeat_changed_rows": False, "repeat_advanced_generators": False,
            "passes": [{"pass": item["pass"], "totals": item["totals"]} for item in passes]}


def generators(cursor: Cursor) -> list[dict[str, Any]]:
    return rows(cursor, """
        SELECT GEN_ID(sync_profile_gen, 0) AS profile_gen,
               GEN_ID(sync_profile_links_gen, 0) AS links_gen,
               GEN_ID(repl$sync_profile_gen, 0) AS repl_profile_gen,
               GEN_ID(repl$sync_profile_links_gen, 0) AS repl_links_gen FROM rdb$database
    """)


def verify(connection: Connection, report: dict[str, Any], codes: list[str],
           uid: int, filial: int, output: Path) -> dict[str, Any]:
    manager = protected_transaction(connection)
    cursor = manager.cursor()
    before = snapshot(cursor)
    result: dict[str, Any] = {"generators_before": generators(cursor), "cases": []}
    try:
        for code in codes:
            strict_sql = seed_sql(report, code, uid, filial, partial=False)
            output.joinpath(f"sync_profile_{code}.sql").write_text(strict_sql, encoding="utf-8")
            strict_before = snapshot(cursor)
            strict_result = rows(cursor, strict_sql)[0]
            if strict_result["status"] == "INCOMPLETE":
                assert snapshot(cursor) == strict_before, "Incomplete profile changed data"
            sql = seed_sql(report, code, uid, filial, partial=True, verification=True)
            first = rows(cursor, sql)[0]
            assert first["status"] in ("COMPLETE", "PARTIAL_VERIFICATION"), first
            first_state = snapshot(cursor)
            first_generators = generators(cursor)
            second = rows(cursor, sql)[0]
            assert second["status"] == first["status"], second
            assert second["inserted_links"] == second["created_profile"] == second["updated_profile"] == 0
            assert snapshot(cursor) == first_state, "Second run changed rows"
            assert generators(cursor) == first_generators, "Second run advanced generators"
            duplicates = rows(cursor, """
                SELECT syncprofid, syncrefid, COUNT(*) AS copies FROM sync_profile_links
                GROUP BY syncprofid, syncrefid HAVING COUNT(*) > 1
            """)
            assert not duplicates, duplicates
            result["cases"].append({"semd_code": code, "strict": strict_result,
                                    "first": first, "second": second,
                                    "rows_identical_on_repeat": True,
                                    "generators_unchanged_on_repeat": True})
        result["generators_after_tests"] = generators(cursor)
    finally:
        if manager.is_active():
            manager.rollback()
        manager.close()
    after = snapshot(connection.cursor())
    assert after == before, "Rollback did not restore profile rows"
    connection.rollback()
    result["profile_rows_restored"] = True
    result["generator_note"] = "Firebird generators advance outside transaction rollback; they were not reset."
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-dsn", required=True)
    parser.add_argument("--fb-database", required=True)
    parser.add_argument("--fb-client", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-codes", nargs="*", default=[])
    parser.add_argument("--export-sql", action="store_true")
    parser.add_argument("--apply-all", action="store_true")
    parser.add_argument("--uid", type=int)
    parser.add_argument("--filial", type=int)
    args = parser.parse_args()
    if (args.verify_codes or args.apply_all) and (not args.uid or not args.filial):
        parser.error("Verification and loading require --uid and --filial from the target MIS")
    driver_config.fb_client_library.value = args.fb_client
    connection = connect(args.fb_database, user=os.environ["ISC_USER"],
                         password=os.environ["ISC_PASSWORD"], charset="UTF8")
    try:
        report = audit(connection, args.pg_dsn)
        write_json(args.output / "coverage.json", report)
        if args.export_sql:
            print(f"SQL exported: {export_sql(report, args.output)}", flush=True)
        if args.verify_codes:
            verification = verify(connection, report, args.verify_codes, args.uid, args.filial, args.output)
            write_json(args.output / "verification.json", verification)
            print(json.dumps(verification, ensure_ascii=False, default=str))
        if args.apply_all:
            applied = apply_catalog(connection, report, args.uid, args.filial, args.output)
            write_json(args.output / "import-result.json", applied)
            print(json.dumps(applied, ensure_ascii=False), flush=True)
        print(json.dumps({"coverage": report["coverage"], "oid_coverage": report["oid_coverage"]},
                         ensure_ascii=False))
    finally:
        if connection.main_transaction.is_active():
            connection.rollback()
        connection.close()


if __name__ == "__main__":
    main()
