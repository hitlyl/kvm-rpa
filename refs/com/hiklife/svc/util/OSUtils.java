/*    */ package com.hiklife.svc.util;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class OSUtils
/*    */ {
/* 11 */   private static final String SYSTEM_TYPE = System.getProperty("os.name").toLowerCase();
/* 12 */   private static final String SYSTEM_ARCH = System.getProperty("os.arch").toLowerCase();
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static boolean isWin() {
/* 20 */     return SYSTEM_TYPE.contains("win");
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static boolean isLinux() {
/* 29 */     return SYSTEM_TYPE.contains("linux");
/*    */   }
/*    */   
/*    */   public static boolean is64Bit() {
/* 33 */     return SYSTEM_ARCH.contains("64");
/*    */   }
/*    */   public static boolean isX86() {
/* 36 */     return (SYSTEM_ARCH.contains("x86") || SYSTEM_ARCH.contains("amd64"));
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/util/OSUtils.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */