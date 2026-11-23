module.exports = {
  extends: ['@commitlint/config-conventional'],
  plugins: [
    {
      rules: {
        'subject-chinese': ({ subject }) => [
          !subject || /\p{Script=Han}/u.test(subject),
          '提交说明须包含中文，type、scope 和代码标识保留原文。',
        ],
      },
    },
  ],
  rules: {
    // 中文说明可以包含 HTTP、SDK 等大小写固定的代码标识。
    'subject-case': [0],
    'subject-chinese': [2, 'always'],
  },
};
