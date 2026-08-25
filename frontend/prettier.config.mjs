/** @type {import('prettier').Config} */
export default {
  plugins: ['prettier-plugin-tailwindcss'],
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  semi: false,
  singleQuote: true,
  trailingComma: 'all',
  bracketSpacing: true,
  arrowParens: 'always',
  tailwindFunctions: ['cn'],
}
