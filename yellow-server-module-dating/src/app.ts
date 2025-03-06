import Data from './data';
import { ApiClient } from './api-client';
import { ModuleAppBase } from 'yellow-server-common';
import path from 'path';

interface LogTopicFilter {
 [key: string]: string;
}

interface Settings {
 web: {
  http_port: number;
  allow_network: boolean;
 };
 database: {
  host: string;
  port: number;
  user: string;
  password: string;
  name: string;
 };
 log: {
  level: string;
  stdout: {
   enabled: boolean;
   levels: LogTopicFilter[];
  };
  file: {
   enabled: boolean;
   name: string;
   levels: LogTopicFilter[];
  };
  database: {
   enabled: boolean;
   level: string;
  };
  json: {
   enabled: boolean;
   name: string;
   level: string;
  };
  elasticsearch: {
   enabled: boolean;
  };
 };
}

class App extends ModuleAppBase {
 defaultSettings: Settings;
 api: ApiClient;
 data: Data;

 constructor() {
  const info = {
   appPath: path.dirname(import.meta.dir) + '/',
   appName: 'Yellow Server Module Dating',
   appVersion: '0.01'
  };
  super(info, path.dirname(__dirname));
  this.defaultSettings = {
   web: {
    http_port: 25003,
    allow_network: false
   },
   database: {
    host: '127.0.0.1',
    port: 3306,
    user: 'dating2',
    password: 'password',
    name: 'dating2'
   },
   log: {
    level: 'info',
    stdout: {
     enabled: true,
     levels: [{ '*': 'info' }]
    },
    file: {
     enabled: true,
     name: 'server.log',
     levels: [{ '*': 'info' }]
    },
    database: {
     enabled: true,
     level: 'debug'
    },
    json: {
     enabled: false,
     name: 'json.log',
     level: 'debug'
    },
    elasticsearch: {
     enabled: false
    }
   }
  };
  this.api = new ApiClient(this);
 }

 async init() {
  this.data = new Data(this.info.settings.database);
 }
}

export default App;
