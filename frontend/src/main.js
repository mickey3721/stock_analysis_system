import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import {
  Button,
  Cell,
  CellGroup,
  NavBar,
  Tabbar,
  TabbarItem,
  Card,
  Tag,
  Icon,
  Search,
  DropdownMenu,
  DropdownItem,
  Empty,
  Loading,
  Divider
} from 'vant'
import 'vant/lib/index.css'

const app = createApp(App)

app.use(router)
app.use(Button)
app.use(Cell)
app.use(CellGroup)
app.use(NavBar)
app.use(Tabbar)
app.use(TabbarItem)
app.use(Card)
app.use(Tag)
app.use(Icon)
app.use(Search)
app.use(DropdownMenu)
app.use(DropdownItem)
app.use(Empty)
app.use(Loading)
app.use(Divider)

app.mount('#app')
