import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Heading from '@theme/Heading';

export type TaskCardItem = {
  title: string;
  to: string;
  description: ReactNode;
};

function TaskCard({title, to, description}: TaskCardItem): ReactNode {
  return (
    <div className="col col--4 margin-bottom--lg">
      <div className="card padding--lg">
        <Heading as="h3"><Link to={to}>{title}</Link></Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function TaskCards({items}: {items: TaskCardItem[]}): ReactNode {
  return (
    <div className="row">
      {items.map((props, idx) => (
        <TaskCard key={idx} {...props} />
      ))}
    </div>
  );
}
