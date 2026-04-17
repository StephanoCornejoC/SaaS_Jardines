/**
 * ESLint configuration for SAAS COREM - React 18 + Vite
 *
 * Stack: React 18, React Router v6, Zustand, Ant Design 5, Axios
 * Herramienta: ESLint 9 (formato legacy .eslintrc para compatibilidad con Vite)
 *
 * Instalacion de dependencias necesarias:
 *   npm install --save-dev \
 *     eslint \
 *     eslint-plugin-react \
 *     eslint-plugin-react-hooks \
 *     eslint-plugin-react-refresh \
 *     @eslint/js
 *
 * Ejecutar: npx eslint . --ext .js,.jsx
 * Con reporte: npx eslint . --ext .js,.jsx --format json -o eslint-report.json
 */

"use strict";

module.exports = {
  root: true,

  env: {
    browser: true,
    es2022: true,
    node: false,
  },

  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },

  settings: {
    react: {
      version: "18",
    },
  },

  extends: [
    // Base ESLint recommended
    "eslint:recommended",
    // React specific rules
    "plugin:react/recommended",
    // React Hooks rules (CRITICO - detecta hooks usados incorrectamente)
    "plugin:react-hooks/recommended",
  ],

  plugins: [
    "react",
    "react-hooks",
    "react-refresh",
  ],

  rules: {
    // ===== REACT CORE =====

    // Detectar imports de React no necesarios (React 18 no requiere import React)
    "react/react-in-jsx-scope": "off",
    "react/jsx-uses-react": "off",

    // PropTypes: warning (proyecto en JS, no TS - mover a error si se migra a TS)
    "react/prop-types": "warn",

    // Keys en listas - CRITICO para performance
    "react/jsx-key": "error",

    // No usar dangerouslySetInnerHTML sin documentacion
    "react/no-danger": "warn",

    // No modificar state directamente
    "react/no-direct-mutation-state": "error",

    // Evitar componentes deprecados
    "react/no-deprecated": "warn",

    // No acceder a string refs (deprecado)
    "react/no-string-refs": "error",

    // No usar findDOMNode (deprecado)
    "react/no-find-dom-node": "error",

    // Cerrar self-closing correctamente
    "react/self-closing-comp": "warn",

    // Fragmentos cortos <> vs <React.Fragment>
    "react/jsx-fragments": ["warn", "syntax"],

    // No indices como keys (performance/bugs)
    "react/no-array-index-key": "warn",

    // Evitar re-renders innecesarios por funciones inline en JSX
    "react/jsx-no-bind": [
      "warn",
      {
        allowArrowFunctions: true,
        allowBind: false,
        ignoreRefs: true,
      },
    ],

    // ===== REACT HOOKS =====

    // Reglas de hooks - NO desactivar, son criticas
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",

    // ===== REACT REFRESH (HMR) =====

    // Solo exportar componentes en modulos (necesario para HMR de Vite)
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],

    // ===== VARIABLES Y SCOPE =====

    // Variables no usadas - CRITICO (F401 equivalente en Python)
    "no-unused-vars": [
      "error",
      {
        vars: "all",
        args: "after-used",
        ignoreRestSiblings: true,
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
      },
    ],

    // Variables no definidas
    "no-undef": "error",

    // No usar var (usar let o const)
    "no-var": "error",

    // Preferir const cuando la variable no se reasigna
    "prefer-const": "error",

    // ===== COMPLEJIDAD =====

    // Complejidad ciclomatica (umbral: 10, alerta: >15)
    "complexity": ["warn", 10],

    // Maxima profundidad de anidamiento
    "max-depth": ["warn", 3],

    // Maxima longitud de funcion (lineas)
    "max-lines-per-function": [
      "warn",
      {
        max: 80,
        skipBlankLines: true,
        skipComments: true,
        IIFEs: true,
      },
    ],

    // Maximo de parametros en funcion
    "max-params": ["warn", 5],

    // ===== SEGURIDAD =====

    // No usar eval()
    "no-eval": "error",

    // No usar new Function() (similar a eval)
    "no-new-func": "error",

    // No usar scripts inline
    "no-script-url": "error",

    // ===== CALIDAD DE CODIGO =====

    // No usar console.log en produccion (permitir warn y error)
    "no-console": ["warn", { allow: ["warn", "error"] }],

    // No tener codigo inalcanzable
    "no-unreachable": "error",

    // No comparar con NaN directamente (usar isNaN)
    "use-isnan": "error",

    // Usar === en lugar de ==
    "eqeqeq": ["error", "always", { null: "ignore" }],

    // No usar comparaciones con undefined (usar typeof)
    "no-undefined": "off",

    // No declarar variables en el mismo scope dos veces
    "no-redeclare": "error",

    // No usar variables antes de declararlas
    "no-use-before-define": [
      "warn",
      { functions: false, classes: true, variables: true },
    ],

    // No tener codigo muerto (else innecesario despues de return)
    "no-else-return": "warn",

    // No tener statements vacios
    "no-empty": "warn",

    // Preferir template literals sobre concatenacion de strings
    "prefer-template": "warn",

    // No usar arguments (usar rest params)
    "prefer-rest-params": "warn",

    // No usar .apply() cuando se puede usar spread
    "prefer-spread": "warn",

    // Evitar debugger statements
    "no-debugger": "error",

    // ===== ASYNC/AWAIT =====

    // Manejar promises correctamente (detecta floating promises)
    "no-promise-executor-return": "error",

    // No usar await en un loop (performance)
    "no-await-in-loop": "warn",

    // Retorno consistente en funciones async
    "require-await": "warn",

    // ===== IMPORTACIONES =====

    // No duplicar imports del mismo modulo
    "no-duplicate-imports": "error",
  },

  overrides: [
    // Configuracion especifica para archivos de configuracion de Vite y Node
    {
      files: ["vite.config.js", "*.config.js", ".eslintrc.cjs"],
      env: {
        node: true,
        browser: false,
      },
      rules: {
        "no-undef": "off",
      },
    },
    // Relajar reglas para archivos de store (Zustand)
    {
      files: ["src/store/**/*.js"],
      rules: {
        // Los stores de Zustand pueden tener funciones de mayor longitud
        "max-lines-per-function": ["warn", 120],
      },
    },
    // Relajar reglas para paginas grandes (componentes de pagina)
    {
      files: ["src/pages/**/*.jsx"],
      rules: {
        // Las paginas pueden tener mas logica de UI
        "max-lines-per-function": ["warn", 200],
        "complexity": ["warn", 15],
      },
    },
  ],

  // Archivos a ignorar
  ignorePatterns: [
    "dist/",
    "node_modules/",
    "public/",
    "*.min.js",
    "coverage/",
  ],
};
