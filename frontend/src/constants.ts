type ModelCost = {
  in: number
  out: number
}

export const MODEL_COST: Record<string, ModelCost> = {
  'gpt-4\\.1-\\d+-\\d+-\\d+': { in: 2, out: 8 },
}

export function costForModel(model: string): ModelCost | undefined {
  for (const key in MODEL_COST) {
    if (model.match(new RegExp(key))) {
      return MODEL_COST[key]
    }
  }
  return undefined
}
