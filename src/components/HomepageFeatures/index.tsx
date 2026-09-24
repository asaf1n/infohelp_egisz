import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  to: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Подключение организации',
    to: '/trunk/egisz/connection/connection-process',
    description: (
      <>
        Этапы внедрения, участники работ и результаты, необходимые для перехода к следующему этапу.
      </>
    ),
  },
  {
    title: 'Проверка и диагностика',
    to: '/trunk/egisz/diagnostics/sql-configuration-check',
    description: (
      <>
        Проверка конфигурации МИС и подготовка сведений для обращения в поддержку.
      </>
    ),
  },
  {
    title: 'Работа службы поддержки',
    to: '/internal/egisz/',
    description: (
      <>
        Регламент ЛТП, предварительная проверка и передача обращения в разработку.
      </>
    ),
  },
];

function Feature({title, to, description}: FeatureItem): ReactNode {
  return (
    <div className="col col--4 margin-bottom--lg">
      <div className="card padding--lg">
        <Heading as="h2"><Link to={to}>{title}</Link></Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
