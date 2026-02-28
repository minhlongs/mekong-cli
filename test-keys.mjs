import { extractAllTranslationKeys } from './scripts/extract-translation-keys.mjs';
const keys = extractAllTranslationKeys('src');
console.log(keys.slice(0, 5));
