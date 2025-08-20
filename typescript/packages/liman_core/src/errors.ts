export class LimanError extends Error {
  public name = "LimanError";
}

export class InvalidSpecError extends LimanError {
  public name = "InvalidSpecError";
}

export class PluginFieldConflictError extends LimanError {
  public name = "PluginFieldConflictError";
}
