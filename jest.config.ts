import type { Config } from "jest";

const config: Config = {
  testEnvironment: "node",

  // ESM + TypeScript
  preset: "ts-jest/presets/default-esm",

  extensionsToTreatAsEsm: [".ts"],

  transform: {
    "^.+\\.ts$": [
      "ts-jest",
      {
        useESM: true,
        tsconfig: "tsconfig.json",
      },
    ],
  },

  moduleNameMapper: {
    // Required for NodeNext + .js imports
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },

  testMatch: [
    "<rootDir>/tests/**/*.test.ts",
  ],

  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
};

export default config;
