import * as k8s from '@pulumi/kubernetes';
import { interpolate } from '@pulumi/pulumi';
import { apiDomain } from './config';
import { namespace } from './namespace';

const name = 'lago';

const deployment = new k8s.apps.v1.Deployment(`${name}-frontend`, {
  metadata: {
    name: 'frontend',
    namespace: namespace.metadata.name,
  },
  spec: {
    replicas: 1,
    selector: {
      matchLabels: {
        app: 'frontend',
      },
    },
    template: {
      metadata: {
        labels: {
          app: 'frontend',
        },
      },
      spec: {
        containers: [
          {
            name: 'frontend',
            image: 'getlago/front:v0.6.1-alpha',
            imagePullPolicy: 'IfNotPresent',
            ports: [{ containerPort: 80 }],
            env: [
              {
                name: 'API_URL',
                value: interpolate`https://${apiDomain}`,
              },
              {
                name: 'CODEGEN_API',
                value: interpolate`https://${apiDomain}`,
              },
              {
                name: 'LAGO_DISABLE_SIGNUP',
                value: 'false',
              },
              {
                name: 'APP_ENV',
                value: 'production',
              },
            ],
          },
        ],
      },
    },
  },
});

export const service = new k8s.core.v1.Service(`${name}-frontend`, {
  metadata: {
    name: 'frontend',
    namespace: namespace.metadata.name,
  },
  spec: {
    ports: [
      {
        port: 80,
      },
    ],
    selector: deployment.spec.selector.matchLabels,
  },
});
