import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElAside,
  ElAlert,
  ElBadge,
  ElButton,
  ElCard,
  ElCheckbox,
  ElContainer,
  ElDatePicker,
  ElDialog,
  ElDivider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoadingDirective,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElSegmented,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTooltip,
  ElTimeSelect,
  ElTimeline,
  ElTimelineItem,
  ElTree,
} from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Bell,
  Calendar,
  Check,
  CircleCheck,
  Compass,
  Connection,
  Cpu,
  DataAnalysis,
  DataBoard,
  DataLine,
  Delete,
  Document,
  Download,
  Files,
  FirstAidKit,
  Folder,
  InfoFilled,
  Key,
  Lightning,
  Loading,
  Lock,
  Location,
  Monitor,
  Odometer,
  OfficeBuilding,
  Opportunity,
  Plus,
  Refresh,
  Setting,
  SwitchButton,
  Tools,
  TrendCharts,
  User,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { installGlobalErrorReporting, reportFrontendError } from './observability/errorReporting'

import './assets/element-plus.css'
// 引入全局样式 (稍后创建)
import './assets/main.css'

const app = createApp(App)
installGlobalErrorReporting()

const icons = {
  ArrowLeft,
  ArrowRight,
  Bell,
  Calendar,
  Check,
  CircleCheck,
  Compass,
  Connection,
  Cpu,
  DataAnalysis,
  DataBoard,
  DataLine,
  Delete,
  Document,
  Download,
  Files,
  FirstAidKit,
  Folder,
  InfoFilled,
  Key,
  Lightning,
  Loading,
  Lock,
  Location,
  Monitor,
  Odometer,
  OfficeBuilding,
  Opportunity,
  Plus,
  Refresh,
  Setting,
  SwitchButton,
  Tools,
  TrendCharts,
  User,
  UserFilled,
  Warning,
}

const elementComponents = [
  ElAside,
  ElAlert,
  ElBadge,
  ElButton,
  ElCard,
  ElCheckbox,
  ElContainer,
  ElDatePicker,
  ElDialog,
  ElDivider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElSegmented,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTooltip,
  ElTimeSelect,
  ElTimeline,
  ElTimelineItem,
  ElTree,
]

for (const component of elementComponents) {
  if (component.name) {
    app.component(component.name, component)
  }
}

for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.directive('loading', ElLoadingDirective)

app.use(createPinia())
app.use(router)

app.config.errorHandler = (error, instance, info) => {
  const componentName = (
    instance as { $?: { type?: { name?: string } } } | null
  )?.$?.type?.name ?? 'anonymous'
  reportFrontendError({
    category: 'vue',
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    url: window.location.href,
    route: window.location.pathname,
    metadata: {
      info,
      component: componentName,
    },
  })
}

app.mount('#app')
