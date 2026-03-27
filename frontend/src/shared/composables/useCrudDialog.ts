import { computed, ref } from 'vue'

type CrudDialogMode = 'create' | 'edit'

interface UseCrudDialogOptions<TItem, TCreateArgs extends unknown[]> {
  createTitle: string
  editTitle: string
  resetForm: (...args: TCreateArgs) => void
  fillForm: (item: TItem) => void
}

export function useCrudDialog<TItem, TCreateArgs extends unknown[] = []>(
  options: UseCrudDialogOptions<TItem, TCreateArgs>
) {
  const dialogVisible = ref(false)
  const dialogType = ref<CrudDialogMode>('create')
  const dialogTitle = computed(() => (
    dialogType.value === 'create' ? options.createTitle : options.editTitle
  ))

  const openCreateDialog = (...args: TCreateArgs) => {
    dialogType.value = 'create'
    options.resetForm(...args)
    dialogVisible.value = true
  }

  const openEditDialog = (item: TItem) => {
    dialogType.value = 'edit'
    options.fillForm(item)
    dialogVisible.value = true
  }

  return {
    dialogVisible,
    dialogType,
    dialogTitle,
    openCreateDialog,
    openEditDialog
  }
}
