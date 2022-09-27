import * as k8s from '@pulumi/kubernetes';
import { namespace } from './namespace';

const name = 'lago';

const deployment = new k8s.apps.v1.Deployment(`${name}-redis`, {
  metadata: {
    name: 'redis',
    namespace: namespace.metadata.name,
  },
  spec: {
    replicas: 1,
    selector: {
      matchLabels: {
        app: 'redis',
      },
    },
    template: {
      metadata: {
        labels: {
          app: 'redis',
        },
      },
      spec: {
        containers: [
          {
            name: 'redis',
            image: 'redis:6.2-alpine',
            imagePullPolicy: 'IfNotPresent',
            ports: [{ containerPort: 6379 }],
          },
        ],
      },
    },
  },
});

export const service = new k8s.core.v1.Service(`${name}-redis`, {
  metadata: {
    name: 'redis',
    namespace: namespace.metadata.name,
  },
  spec: {
    ports: [
      {
        port: 6379,
      },
    ],
    selector: deployment.spec.selector.matchLabels,
  },
});
