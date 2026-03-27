import type { Ref } from 'vue'

type CrudDialogMode = 'create' | 'edit'

interface UseCrudSubmitOptions {
  dialogType: Ref<CrudDialogMode>
  dialogVisible: Ref<boolean>
  createAction: () => Promise<void>
  updateAction: () => Promise<void>
  onSuccess?: () => void
}

export function useCrudSubmit(options: UseCrudSubmitOptions) {
  const submit = async () => {
    if (options.dialogType.value === 'create') {
      await options.createAction()
    } else {
      await options.updateAction()
    }

    options.dialogVisible.value = false
    options.onSuccess?.()
  }

  return {
    submit
  }
}
