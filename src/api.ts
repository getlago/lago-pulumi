import * as k8s from '@pulumi/kubernetes';
import { interpolate } from '@pulumi/pulumi';
import { frontendDomain, rsaPrivateKey, secretKeyBase } from './config';
import { namespace } from './namespace';
import {
  databaseName,
  databasePassword,
  service as databaseService,
  databaseUser,
} from './postgres';
import { service as redisService } from './redis';

const name = 'lago';

const databaseHost = interpolate`${databaseService.metadata.name}.${databaseService.metadata.namespace}`;
const databaseUrl = interpolate`postgresql://${databaseUser}:${databasePassword}@${databaseHost}:5432/${databaseName}`;

const redisHost = interpolate`${redisService.metadata.name}.${redisService.metadata.namespace}`;
const redisUrl = interpolate`redis://${redisHost}:6379`;

const deployment = new k8s.apps.v1.Deployment(`${name}-deployment`, {
  metadata: {
    name: 'api',
    namespace: namespace.metadata.name,
  },
  spec: {
    replicas: 1,
    selector: {
      matchLabels: {
        app: 'api',
      },
    },
    template: {
      metadata: {
        labels: {
          app: 'api',
        },
      },
      spec: {
        containers: [
          {
            name: 'api',
            image: 'getlago/api:v0.6.1-alpha',
            imagePullPolicy: 'IfNotPresent',
            ports: [{ containerPort: 3000 }],
            env: [
              {
                name: 'DATABASE_URL',
                value: databaseUrl,
              },
              {
                name: 'REDIS_URL',
                value: redisUrl,
              },
              {
                name: 'LAGO_REDIS_CACHE_URL',
                value: redisUrl,
              },
              {
                name: 'SECRET_KEY_BASE',
                value: secretKeyBase,
              },
              {
                name: 'RAILS_ENV',
                value: 'production',
              },
              {
                name: 'LAGO_FRONT_URL',
                value: interpolate`https://${frontendDomain}`,
              },
              {
                // TODO: Replace and move to a secret
                name: 'RSA_PRIVATE_KEY',
                value: rsaPrivateKey,
              },
              {
                // TODO: Replace and move to a secret
                name: 'LAGO_RSA_PRIVATE_KEY',
                value: rsaPrivateKey,
              },
              {
                // TODO: Replace and move to a secret
                name: 'ENCRYPTION_PRIMARY_KEY',
                value: 'not-a-secret',
              },
              {
                // TODO: Replace and move to a secret
                name: 'ENCRYPTION_DETERMINISTIC_KEY',
                value: 'not-a-secret',
              },
              {
                // TODO: Replace and move to a secret
                name: 'ENCRYPTION_KEY_DERIVATION_SALT',
                value: 'not-a-secret',
              },
              {
                name: 'LAGO_USE_AWS_S3',
                value: 'false',
              },
              {
                // TODO: Replace with actual instance of gotenberg
                name: 'LAGO_PDF_URL',
                value: 'not-a-service',
              },
              {
                name: 'LAGO_DISABLE_SEGMENT',
                value: 'true',
              },
              {
                name: 'LAGO_AWS_S3_ACCESS_KEY_ID',
                value: 'not-a-secret',
              },
              {
                name: 'LAGO_AWS_S3_SECRET_ACCESS_KEY',
                value: 'not-a-secret',
              },
              {
                name: 'LAGO_AWS_S3_REGION',
                value: 'not-a-region',
              },
              {
                name: 'LAGO_AWS_S3_BUCKET',
                value: 'not-a-bucket',
              },
            ],
          },
        ],
      },
    },
  },
});

export const service = new k8s.core.v1.Service(`${name}-api`, {
  metadata: {
    name: 'api',
    namespace: namespace.metadata.name,
  },
  spec: {
    ports: [
      {
        port: 3000,
      },
    ],
    selector: deployment.spec.selector.matchLabels,
  },
});
