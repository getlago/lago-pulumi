import { Config } from '@pulumi/pulumi';

const config = new Config();

export const frontendDomain = config.require('frontendDomain');
export const apiDomain = config.require('apiDomain');

export const secretKeyBase = config.requireSecret('secret-key');
export const rsaPrivateKey = config.requireSecret('rsa-private-key');
