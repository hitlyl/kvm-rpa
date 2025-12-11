/*    */ package com.hiklife.svc.viewer;
/*    */ 
/*    */ import java.util.concurrent.Executors;
/*    */ import java.util.concurrent.ScheduledExecutorService;
/*    */ import java.util.concurrent.TimeUnit;

import refs.com.hiklife.svc.viewer.WorkThreadPool;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class WorkThreadPool
/*    */ {
/* 24 */   private final ScheduledExecutorService scheduledThreadPool = Executors.newScheduledThreadPool(1);
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static WorkThreadPool getInstance() {
/* 33 */     return WorkThreadPoolHolder.instance;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void execute(Runnable runnable) {
/* 42 */     this.scheduledThreadPool.execute(runnable);
/*    */   }
/*    */   public void execute(Runnable runnable, long delay) {
/* 45 */     this.scheduledThreadPool.schedule(runnable, delay, TimeUnit.MILLISECONDS);
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   private WorkThreadPool() {}
/*    */ 
/*    */ 
/*    */   
/*    */   private static class WorkThreadPoolHolder
/*    */   {
/* 56 */     private static final WorkThreadPool instance = new WorkThreadPool();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/WorkThreadPool.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */