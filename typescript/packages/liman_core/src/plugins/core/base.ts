export type Plugin = {
  readonly name: string;
  readonly appliesTo: readonly string[];
  readonly registeredKinds: readonly string[];
  readonly fieldName: string;
  readonly fieldType: unknown;
  validate(specData: unknown): unknown;
};
