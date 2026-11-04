module.exports = {
  // 按工程实际源码范围调整 glob；与全量 lint / format 检查范围一致。
  '**/*.{js,jsx,ts,tsx,mjs,cjs}': [
    'eslint --max-warnings=0 --no-warn-ignored',
    'prettier --check',
  ],
};
