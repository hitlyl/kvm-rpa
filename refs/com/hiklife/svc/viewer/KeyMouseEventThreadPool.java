/*    */ package com.hiklife.svc.viewer;
/*    */ 
/*    */ import java.util.concurrent.ExecutorService;
/*    */ import java.util.concurrent.Executors;

import refs.com.hiklife.svc.viewer.KeyMouseEventThreadPool;
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
/*    */ public class KeyMouseEventThreadPool
/*    */ {
/* 22 */   private final ExecutorService fixedThreadPool = Executors.newFixedThreadPool(1);
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static KeyMouseEventThreadPool getInstance() {
/* 30 */     return KeyMouseEventThreadPoolHolder.instance;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void execute(Runnable runnable) {
/* 38 */     this.fixedThreadPool.execute(runnable);
/*    */   }
/*    */ 
/*    */   
/*    */   private KeyMouseEventThreadPool() {}
/*    */   
/*    */   private static class KeyMouseEventThreadPoolHolder
/*    */   {
/* 46 */     private static final KeyMouseEventThreadPool instance = new KeyMouseEventThreadPool();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/KeyMouseEventThreadPool.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */