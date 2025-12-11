/*    */ package com.hiklife.svc.viewer;

import refs.com.hiklife.svc.viewer.Option;

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
/*    */ public class Option
/*    */ {
/* 16 */   public static Option instance = new Option();
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getEnableHideLocalMouse() {
/* 24 */     return this.enableHideLocalMouse;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setEnableHideLocalMouse(int enableHideLocalMouse) {
/* 32 */     this.enableHideLocalMouse = enableHideLocalMouse;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getEnableImageScale() {
/* 40 */     return this.enableImageScale;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setEnableImageScale(int enableImageScale) {
/* 48 */     this.enableImageScale = enableImageScale;
/*    */   }
/*    */   
/*    */   public int getEnableFullScreen() {
/* 52 */     return this.enableFullScreen;
/*    */   }
/*    */   
/*    */   public void setEnableFullScreen(int enableFullScreen) {
/* 56 */     this.enableFullScreen = enableFullScreen;
/*    */   }
/*    */   
/*    */   public double getMouseSensitivity() {
/* 60 */     return this.mouseSensitivity;
/*    */   }
/*    */   
/*    */   public void setMouseSensitivity(double mouseSensitivity) {
/* 64 */     this.mouseSensitivity = mouseSensitivity;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */   
/* 70 */   private int enableHideLocalMouse = 0;
/*    */ 
/*    */ 
/*    */   
/* 74 */   private int enableImageScale = 1;
/*    */ 
/*    */ 
/*    */   
/* 78 */   private int enableFullScreen = 0;
/*    */   
/* 80 */   private double mouseSensitivity = 1.5D;
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/Option.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */