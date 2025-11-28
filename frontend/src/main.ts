import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import App from './App.vue'
import { loadNodeConfigs } from './config/nodes'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 预加载节点配置后再挂载应用
loadNodeConfigs().then((success) => {
  if (success) {
    console.log('节点配置已预加载')
  } else {
    console.warn('节点配置预加载失败，将使用后备配置')
  }
  app.mount('#app')
}).catch(error => {
  console.error('节点配置加载失败:', error)
  // 即使失败也挂载应用
  app.mount('#app')
})

