import { BarChart3, Bell, Bike, Box, ChevronDown, CircleDollarSign, ClipboardList, LayoutDashboard, Menu, Moon, Radio, Route, Store, Sun, Warehouse, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { IconButton, SearchField } from './components'

const items:{name:string;icon:LucideIcon;page?:Page}[]=[
 {name:'Dashboard',icon:LayoutDashboard,page:'dashboard'},
 {name:'Orders',icon:Box,page:'orders'},
 {name:'Riders',icon:Bike,page:'riders'},
 {name:'Vendors',icon:Store,page:'vendors'},
 {name:'Tracking',icon:Route},
 {name:'Analytics',icon:BarChart3},
 {name:'Billing',icon:CircleDollarSign},
 {name:'Tasks',icon:ClipboardList},
]
const titles:Record<Page,string>={dashboard:'Control Center',orders:'Orders Command',riders:'Rider Dispatch',vendors:'Vendor Network',styleguide:'Design System'}
export type Page='dashboard'|'vendors'|'orders'|'riders'|'styleguide'

export function Sidebar({open,onClose,page,onNavigate}:{open:boolean;onClose:()=>void;page:Page;onNavigate:(page:Page)=>void}){return <aside className={`sidebar ${open?'open':''}`}><div className="sidebar-network"/><div className="brand"><span className="brand-mark"><Warehouse/></span><span><strong>LEE LOGISTICS</strong><small>Operations Platform</small></span><IconButton label="Close navigation" className="mobile-close" onClick={onClose}><X size={17}/></IconButton></div><nav className="command-nav"><p>COMMAND NETWORK</p>{items.map(({name,icon:Icon,page:destination})=><button key={name} className={page===destination?'active':''} onClick={()=>destination&&onNavigate(destination)}><Icon/><span>{name}</span>{page===destination&&<i/>}</button>)}</nav><div className="sidebar-status"><Radio/><div><span>Dispatch network</span><strong>All systems nominal</strong></div><i/></div><button className={`styleguide-link ${page==='styleguide'?'active':''}`} onClick={()=>onNavigate('styleguide')}>Interface system</button></aside>}

export function Topbar({onMenu,theme,setTheme,onSearch,onAdd,page}:{onMenu:()=>void;theme:string;setTheme:()=>void;onSearch:(q:string)=>void;onAdd:()=>void;page:Page}){return <header className="topbar"><div className="topbar-section"><IconButton label="Open navigation" className="mobile-menu" onClick={onMenu}><Menu/></IconButton><div><small>OPERATIONS / {page.toUpperCase()}</small><strong>{titles[page]}</strong></div></div>{page!=='dashboard'&&<SearchField value="" onChange={onSearch} placeholder={page==='orders'?'Search shipments…':page==='riders'?'Search rider network…':'Search vendor network…'}/>}<div className="top-actions"><span className="operations-online"><i/> SYSTEM LIVE</span><IconButton label="Toggle theme" onClick={setTheme}>{theme==='light'?<Moon/>:<Sun/>}</IconButton>{page==='vendors'&&<button className="add" onClick={onAdd}>+ Add vendor</button>}<IconButton label="Notifications" className="notification-button"><Bell/><i/></IconButton><button className="user"><span className="user-avatar">DV</span><span><strong>David</strong><small>Administrator</small></span><ChevronDown/></button></div></header>}
