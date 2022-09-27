import * as k8s from '@pulumi/kubernetes';
import { namespace } from './namespace';

const name = 'lago';
export const databaseName = 'billing';
export const databaseUser = 'billing-user';
export const databasePassword = 'not-a-secret';

const deployment = new k8s.apps.v1.Deployment(`${name}-postgres`, {
  metadata: {
    name: 'postgres',
    namespace: namespace.metadata.name,
  },
  spec: {
    replicas: 1,
    selector: {
      matchLabels: {
        app: 'postgres',
      },
    },
    template: {
      metadata: {
        labels: {
          app: 'postgres',
        },
      },
      spec: {
        containers: [
          {
            name: 'postgres',
            image: 'postgres:14.0-alpine',
            imagePullPolicy: 'IfNotPresent',
            ports: [{ containerPort: 5432 }],
            env: [
              {
                name: 'POSTGRES_DB',
                value: databaseName,
              },
              {
                name: 'POSTGRES_USER',
                value: databaseUser,
              },
              {
                name: 'POSTGRES_PASSWORD',
                value: databasePassword,
              },
              {
                name: 'PGDATA',
                value: '/data/postgres',
              },
            ],
          },
        ],
      },
    },
  },
});

export const service = new k8s.core.v1.Service(`${name}-postgres`, {
  metadata: {
    name: 'postgres',
    namespace: namespace.metadata.name,
  },
  spec: {
    ports: [
      {
        port: 5432,
      },
    ],
    selector: deployment.spec.selector.matchLabels,
  },
});
