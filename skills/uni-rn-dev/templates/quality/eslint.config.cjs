const { fixupConfigRules } = require('@eslint/compat');
const reactNativeConfig = require('@react-native/eslint-config/flat');
const globals = require('globals');

const namingConvention = [
  // React 组件、构造器联合类型和 Context 需要保留 PascalCase 绑定。
  { selector: 'variable', format: ['camelCase', 'PascalCase'] },
  {
    selector: 'variable',
    types: ['boolean', 'string', 'number', 'array'],
    format: ['camelCase'],
  },
  {
    selector: 'variable',
    modifiers: ['global', 'const'],
    format: ['camelCase', 'PascalCase', 'UPPER_CASE'],
  },
  {
    selector: 'variable',
    modifiers: ['global', 'const'],
    types: ['boolean', 'string', 'number', 'array'],
    format: ['camelCase', 'UPPER_CASE'],
  },
  { selector: 'function', format: ['camelCase', 'PascalCase'] },
  {
    selector: 'parameter',
    format: ['camelCase', 'PascalCase'],
    leadingUnderscore: 'allow',
  },
  { selector: 'typeLike', format: ['PascalCase'] },
  {
    selector: 'interface',
    format: ['PascalCase'],
    custom: { regex: '^I[A-Z]', match: false },
  },
  // 导入名称和对象成员可能来自 SDK 或外部协议，不改写其公开契约。
  { selector: 'import', format: ['camelCase', 'PascalCase', 'UPPER_CASE'] },
  { selector: 'memberLike', format: null },
  {
    selector: ['variable', 'parameter'],
    modifiers: ['destructured'],
    filter: { regex: '.*', match: true },
    format: null,
  },
];

module.exports = [
  {
    // naming-convention 跳过具名导入；仅补查本地改名，不约束来源 API 的名称。
    plugins: {
      'rn-quality': {
        rules: {
          'import-alias-case': {
            meta: {
              type: 'suggestion',
              schema: [],
              messages: {
                format:
                  '本地导入别名使用 camelCase、PascalCase 或 UPPER_SNAKE_CASE。',
              },
            },
            create(context) {
              return {
                ImportSpecifier(node) {
                  const original = node.imported.name ?? node.imported.value;
                  const alias = node.local.name;
                  if (original === alias) {
                    return;
                  }
                  const first = alias[0];
                  const camelOrPascal =
                    !alias.includes('_') &&
                    (first === first.toLowerCase() ||
                      first === first.toUpperCase());
                  const upperSnake =
                    alias === alias.toUpperCase() &&
                    alias.split('_').every(part => part.length > 0);
                  const valid = camelOrPascal || upperSnake;
                  if (!valid) {
                    context.report({ node: node.local, messageId: 'format' });
                  }
                },
              };
            },
          },
        },
      },
    },
    rules: { 'rn-quality/import-alias-case': 'error' },
  },
  {
    ignores: ['**/node_modules/**', '**/coverage/**', 'android/**', 'ios/**'],
  },
  {
    files: ['**/*.{js,mjs,cjs}', '__tests__/**/*.{ts,tsx}'],
    languageOptions: {
      globals: { ...globals.node, ...globals.jest },
    },
  },
  // ft-flow 仍使用旧 context API，由 ESLint 官方工具保留其规则行为。
  ...fixupConfigRules(reactNativeConfig),
  {
    files: ['**/*.{js,mjs,cjs}'],
    rules: {
      camelcase: ['error', { properties: 'never', ignoreImports: true }],
    },
  },
  {
    rules: {
      // RN 的 Prettier 兼容配置关闭了 curly；项目要求所有控制语句保留大括号。
      curly: ['error', 'all'],
      'no-nested-ternary': 'error',
      // 在 RN 预设之上采用通用检查；保留目标工程更严格的有效规则。
      'array-callback-return': 'error',
      'for-direction': 'error',
      'guard-for-in': 'error',
      'no-async-promise-executor': 'error',
      'no-case-declarations': 'error',
      'no-dupe-else-if': 'error',
      'no-duplicate-case': 'error',
      'no-param-reassign': 'error',
      'no-promise-executor-return': 'error',
      'no-self-assign': 'error',
      'no-unsafe-finally': 'error',
      'no-unused-labels': 'error',
      'no-useless-catch': 'error',
      'no-var': 'error',
      'require-yield': 'error',
      'prefer-const': 'error',
      // 当前 ESLint 核心规则已支持 TS，替代已弃用的 TS 扩展规则。
      'no-loop-func': 'error',
      'react/jsx-key': 'error',
      'react/no-children-prop': 'error',
      'react/no-deprecated': 'error',
      'react/no-direct-mutation-state': 'error',
      'react/no-is-mounted': 'error',
      'react/no-unescaped-entities': 'error',
      'react/require-render-return': 'error',
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parserOptions: {
        // 类型收窄检查使用所属 tsconfig 的真实类型信息。
        projectService: true,
        tsconfigRootDir: __dirname,
      },
    },
    rules: {
      '@typescript-eslint/naming-convention': ['error', ...namingConvention],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-unsafe-type-assertion': 'error',
      // Umi 使用的旧 ban-types / no-empty-interface 在 v8 中拆分为以下规则。
      '@typescript-eslint/no-empty-object-type': 'error',
      '@typescript-eslint/no-wrapper-object-types': 'error',
      '@typescript-eslint/no-unsafe-function-type': 'error',
      '@typescript-eslint/no-confusing-non-null-assertion': 'error',
      'no-dupe-class-members': 'off',
      '@typescript-eslint/no-dupe-class-members': 'error',
      'no-invalid-this': 'off',
      '@typescript-eslint/no-invalid-this': 'error',
      '@typescript-eslint/no-misused-new': 'error',
      '@typescript-eslint/no-namespace': 'error',
      '@typescript-eslint/no-non-null-asserted-optional-chain': 'error',
      'no-redeclare': 'off',
      '@typescript-eslint/no-redeclare': 'error',
      '@typescript-eslint/no-this-alias': 'error',
      'no-unused-expressions': 'off',
      '@typescript-eslint/no-unused-expressions': 'error',
      'no-use-before-define': 'off',
      // 保留函数声明提升；变量、类和枚举仍须先定义再使用。
      '@typescript-eslint/no-use-before-define': [
        'error',
        { functions: false },
      ],
      'no-useless-constructor': 'off',
      '@typescript-eslint/no-useless-constructor': 'error',
      '@typescript-eslint/triple-slash-reference': 'error',
    },
  },
  {
    files: ['**/constants{,.native,.ios,.android,.web}.ts'],
    rules: {
      '@typescript-eslint/naming-convention': [
        'error',
        ...namingConvention,
        {
          selector: 'variable',
          modifiers: ['global', 'const'],
          // 文件角色明确固定常量；局部运行值及其他文件的 const 不受此约束。
          filter: { regex: '.*', match: true },
          format: ['UPPER_CASE'],
        },
        {
          selector: 'variable',
          modifiers: ['global', 'const', 'destructured'],
          filter: { regex: '.*', match: true },
          format: null,
        },
      ],
    },
  },
  {
    // 只约束测试用例，__tests__ 中可复用的 fixture 仍允许导出。
    files: ['**/*.{test,spec,unit,e2e}.{js,jsx,ts,tsx}'],
    rules: {
      'jest/no-conditional-expect': 'error',
      'jest/no-deprecated-functions': 'error',
      'jest/no-export': 'error',
      'jest/no-focused-tests': 'error',
      'jest/no-identical-title': 'error',
      'jest/no-interpolation-in-snapshots': 'error',
      'jest/no-jasmine-globals': 'error',
      'jest/no-mocks-import': 'error',
      'jest/no-standalone-expect': 'error',
      'jest/valid-describe-callback': 'error',
      'jest/valid-expect-in-promise': 'error',
      'jest/valid-expect': 'error',
      'jest/valid-title': 'error',
    },
  },
];
