export type LanguageCode =
  | "en"
  | "ru"
  | "zh"
  | "fr"
  | "de"
  | "es"
  | "it"
  | "pt"
  | "ja"
  | "ko";

const VALID_LANGUAGE_CODES = [
  "en",
  "ru",
  "zh",
  "fr",
  "de",
  "es",
  "it",
  "pt",
  "ja",
  "ko",
] as const;

export function isValidLanguageCode(code: string): code is LanguageCode {
  return VALID_LANGUAGE_CODES.includes(code as LanguageCode);
}
