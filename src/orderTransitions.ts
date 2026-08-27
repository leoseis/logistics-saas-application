import type { ApiOrderStatus } from './api'

export type OrderTransitionAction =
 | {kind:'assign';label:'Assign rider'}
 | {kind:'verify';label:'Verify pickup'}
 | {kind:'status';label:'Mark as delivered';status:'delivered'}
 | {kind:'cancel';label:'Cancel order';status:'cancelled'}

const actions:Record<ApiOrderStatus,OrderTransitionAction[]>={
 pending:[{kind:'assign',label:'Assign rider'},{kind:'cancel',label:'Cancel order',status:'cancelled'}],
 assigned:[{kind:'verify',label:'Verify pickup'},{kind:'cancel',label:'Cancel order',status:'cancelled'}],
 picked_up:[{kind:'status',label:'Mark as delivered',status:'delivered'}],
 delivered:[],
 cancelled:[],
}

export const getOrderTransitionActions=(status:ApiOrderStatus)=>actions[status]
