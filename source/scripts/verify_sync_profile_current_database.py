"""Verify the exported Firebird statements against reversible profile discrepancies."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Any

from firebird.driver import DatabaseError

from sync_profile_seed import connect, driver_config, generators, protected_transaction, rows, snapshot, write_json


def verify(database: str, client: str, sql_file: Path, output: Path) -> None:
    driver_config.fb_client_library.value = client
    connection = connect(database, user=os.environ["ISC_USER"],
                         password=os.environ["ISC_PASSWORD"], charset="UTF8")
    sql = sql_file.read_text(encoding="utf-8")
    marker = "EXECUTE BLOCK RETURNS"
    blocks = [part[part.index(marker):].strip() for part in sql.split("^") if marker in part]
    assert len(blocks) == sql.count(marker)
    block = next(part for part in blocks if "syncprofident = '227'" in part)
    results: list[dict[str, Any]] = []
    try:
        initial = snapshot(connection.cursor())
        connection.rollback()
        for case in ("unchanged", "missing_links", "empty_profile", "changed_metadata",
                     "missing_source_reference", "conflicting_procedure", "duplicate_link"):
            manager = protected_transaction(connection)
            cursor = manager.cursor()
            try:
                profile = rows(cursor, "SELECT * FROM sync_profile WHERE syncprofident = '227'")[0]
                profile_id = profile["syncprofid"]
                links = rows(cursor, f"SELECT * FROM sync_profile_links WHERE syncprofid = {profile_id} ORDER BY syncproflinkid")
                original_refs = {item["syncrefid"] for item in links}
                if case in ("missing_links", "empty_profile", "missing_source_reference"):
                    selected = links if case == "empty_profile" else links[:3]
                    for item in selected:
                        cursor.execute("DELETE FROM sync_profile_links WHERE syncproflinkid = ?", (item["syncproflinkid"],))
                if case == "changed_metadata":
                    cursor.execute("UPDATE sync_profile SET syncprofname = ?, comment = ? WHERE syncprofid = ?",
                                   ("Проверка восстановления имени", "Проверка восстановления комментария", profile_id))
                if case == "missing_source_reference":
                    cursor.execute("UPDATE sync_reference SET disabled = 1 WHERE syncrefid = ?", (links[0]["syncrefid"],))
                if case == "conflicting_procedure":
                    cursor.execute("UPDATE sync_profile SET syncprof_sp = 'SYNC_PROFILE_GET_DEFAULT' WHERE syncprofid = ?", (profile_id,))
                if case == "duplicate_link":
                    cursor.execute("INSERT INTO sync_profile_links (syncproflinkid, syncprofid, syncrefid) VALUES (GEN_ID(sync_profile_links_gen, 1), ?, ?)",
                                   (profile_id, links[0]["syncrefid"]))
                if case in ("conflicting_procedure", "duplicate_link"):
                    before_error = snapshot(cursor)
                    try:
                        rows(cursor, block)
                    except DatabaseError as error:
                        expected = "PROFILE_REQUIRES_REVIEW" if case == "conflicting_procedure" else "DUPLICATE_LINKS"
                        assert expected in str(error), str(error)
                    else:
                        raise AssertionError("Conflicting profile was silently changed")
                    assert snapshot(cursor) == before_error
                    results.append({"case": case, "result": expected, "no_changes_after_error": True})
                    continue
                first = rows(cursor, block)[0]
                assert first["profile_id"] == profile_id
                assert first["status"] == "PARTIAL_SOURCE"
                expected_insertions = {"unchanged": 0, "missing_links": 3, "empty_profile": len(links),
                                       "changed_metadata": 0, "missing_source_reference": 2}[case]
                assert first["inserted_links"] == expected_insertions, first
                expected_refs = original_refs - ({links[0]["syncrefid"]} if case == "missing_source_reference" else set())
                restored = rows(cursor, f"SELECT syncrefid FROM sync_profile_links WHERE syncprofid = {profile_id}")
                assert {item["syncrefid"] for item in restored} == expected_refs
                assert len(restored) == len(expected_refs)
                repaired_profile = rows(cursor, f"SELECT * FROM sync_profile WHERE syncprofid = {profile_id}")[0]
                for field in ("uid", "filial", "parent_syncprofid", "repl$id", "repl$grpid"):
                    assert repaired_profile[field] == profile[field]
                if case == "changed_metadata":
                    assert repaired_profile["syncprofname"] == profile["syncprofname"]
                    assert repaired_profile["comment"] == profile["comment"]
                    assert first["updated_profile"] == 1
                state, gen = snapshot(cursor), generators(cursor)
                second = rows(cursor, block)[0]
                assert all(second[key] == 0 for key in ("created_profile", "updated_profile", "inserted_links"))
                assert snapshot(cursor) == state and generators(cursor) == gen
                result = {"case": case, "first": first, "repeat_no_changes": True}
                if case == "missing_source_reference":
                    cursor.execute("UPDATE sync_reference SET disabled = ? WHERE syncrefid = ?",
                                   (None, links[0]["syncrefid"]))
                    recovered = rows(cursor, block)[0]
                    assert recovered["inserted_links"] == 1
                    assert recovered["mapped_count"] == len(links)
                    state, gen = snapshot(cursor), generators(cursor)
                    rows(cursor, block)
                    assert snapshot(cursor) == state and generators(cursor) == gen
                    result["source_restored_link_added"] = True
                results.append(result)
            finally:
                manager.rollback()
                manager.close()
            assert snapshot(connection.cursor()) == initial
            connection.rollback()
        manager = protected_transaction(connection)
        try:
            cursor = manager.cursor()
            before, gen = snapshot(cursor), generators(cursor)
            for pass_number in (1, 2):
                total = {key: 0 for key in ("created_profile", "updated_profile", "inserted_links")}
                for statement in blocks:
                    result = rows(cursor, statement)[0]
                    for key in total:
                        total[key] += result[key]
                assert all(value == 0 for value in total.values()), total
                assert snapshot(cursor) == before and generators(cursor) == gen
                results.append({"case": "full_catalog", "pass": pass_number, "blocks": len(blocks),
                                "totals": total, "rows_and_generators_unchanged": True})
        finally:
            manager.rollback()
            manager.close()
        assert snapshot(connection.cursor()) == initial
        connection.rollback()
        write_json(output, {"database": database, "sql_sha256": hashlib.sha256(sql_file.read_bytes()).hexdigest(),
                            "profiles": len(initial["profiles"]), "links": len(initial["links"]),
                            "all_test_changes_rolled_back": True, "cases": results,
                            "generator_note": "Insertion tests advance generators outside rollback; no resets performed."})
        print(f"PASS: {len(results)} checks; database rows restored; report: {output}", flush=True)
    finally:
        if connection.main_transaction.is_active():
            connection.rollback()
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--sql", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.database, args.client, args.sql, args.output)


if __name__ == "__main__":
    main()
