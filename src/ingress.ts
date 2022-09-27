import * as k8s from '@pulumi/kubernetes';
import { service as apiService } from './api';
import { apiDomain, frontendDomain } from './config';
import { service as frontendService } from './frontend';
import { namespace } from './namespace';

const name = 'lago';

export const ingress = new k8s.networking.v1.Ingress(`${name}-ingress`, {
  metadata: {
    name: 'api',
    namespace: namespace.metadata.name,
    annotations: {
      'kubernetes.io/ingress.class': 'caddy',
    },
  },
  spec: {
    rules: [
      {
        host: apiDomain,
        http: {
          paths: [
            {
              path: '/',
              pathType: 'Prefix',
              backend: {
                service: {
                  name: apiService.metadata.name,
                  port: { number: 3000 },
                },
              },
            },
          ],
        },
      },
      {
        host: frontendDomain,
        http: {
          paths: [
            {
              path: '/',
              pathType: 'Prefix',
              backend: {
                service: {
                  name: frontendService.metadata.name,
                  port: { number: 80 },
                },
              },
            },
          ],
        },
      },
    ],
  },
});
