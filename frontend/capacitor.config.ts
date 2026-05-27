import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.readafterme.app',
  appName: 'ReadAfterMe',
  webDir: 'dist',
  server: {
    url: 'http://10.0.0.233:9004',
    cleartext: true,
  },
};

export default config;
