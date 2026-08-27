import type { ReactNode } from 'react'
import { Bike, Check, MapPin, Navigation, Package, ShieldCheck } from 'lucide-react'
import type { ApiOrderStatus } from './api'
import { Button } from './components'

export function PageHero({eyebrow,title,description,action}:{eyebrow:string;title:string;description:string;action?:()=>void}){const brandedEyebrow=eyebrow==='Logistics control center'?'LEE Logistics control center':eyebrow;return <section className="command-hero"><div className="hero-grid"/><div className="route-signal"><i/><span/><b/></div><div className="hero-copy"><span className="hero-kicker"><i/> {brandedEyebrow}</span><h1>{title}</h1><p>{description}</p>{action&&<Button className="hero-action" variant="primary" onClick={action}>+ Create Order</Button>}</div><div className="hero-telemetry"><span><i/> LEE Network</span><strong>OPERATIONS ONLINE</strong></div></section>}

export function SectionHeader({eyebrow,title,description,aside}:{eyebrow?:string;title:string;description?:string;aside?:ReactNode}){return <div className="section-header"><div>{eyebrow&&<span>{eyebrow}</span>}<h2>{title}</h2>{description&&<p>{description}</p>}</div>{aside}</div>}

export function RouteDisplay({pickup,destination,compact=false}:{pickup:string;destination:string;compact?:boolean}){return <div className={`route-display ${compact?'compact':''}`}><span><MapPin/> <b>Pickup</b><em>{pickup}</em></span><i><Navigation/></i><span><MapPin/> <b>Destination</b><em>{destination}</em></span></div>}

const stages=[{status:'pending',label:'Order received',icon:Package},{status:'assigned',label:'Rider assigned',icon:Bike},{status:'picked_up',label:'Pickup verified',icon:ShieldCheck},{status:'delivered',label:'Delivered',icon:Check}] as const
const rank:Record<ApiOrderStatus,number>={pending:0,assigned:1,picked_up:2,delivered:3,cancelled:-1}
export function ShipmentTimeline({status}:{status:ApiOrderStatus}){const current=rank[status];return <div className={`shipment-timeline ${status==='cancelled'?'is-cancelled':''}`}>{stages.map(({status:stage,label,icon:Icon},index)=><div className={index<=current?'complete':''} key={stage}><span><Icon/></span><small>{label}</small></div>)}</div>}

export function LoadingSkeleton({rows=4}:{rows?:number}){return <div className="loading-skeleton" aria-label="Loading">{Array.from({length:rows},(_,index)=><i key={index}/>)}</div>}
