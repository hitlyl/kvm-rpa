/*    */ package com.hiklife.svc.viewer;
/*    */ 
/*    */ import java.util.concurrent.ExecutorService;
/*    */ import java.util.concurrent.Executors;

import refs.com.hiklife.svc.viewer.AudioPlayThreadPool;
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
/*    */ 
/*    */ public class AudioPlayThreadPool
/*    */ {
/* 24 */   private final ExecutorService fixedThreadPool = Executors.newFixedThreadPool(1);
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static AudioPlayThreadPool getInstance() {
/* 33 */     return AudioPlayThreadPoolHolder.instance;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void execute(Runnable runnable) {
/* 42 */     this.fixedThreadPool.execute(runnable);
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   private AudioPlayThreadPool() {}
/*    */ 
/*    */ 
/*    */   
/*    */   private static class AudioPlayThreadPoolHolder
/*    */   {
/* 53 */     private static final AudioPlayThreadPool instance = new AudioPlayThreadPool();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/AudioPlayThreadPool.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */