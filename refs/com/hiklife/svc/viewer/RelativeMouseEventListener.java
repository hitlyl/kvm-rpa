/*     */ package com.hiklife.svc.viewer;
/*     */ import java.awt.Point;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeMouseListener;
import refs.com.hiklife.svc.viewer.KeyMouseEventThreadPool;
import refs.com.hiklife.svc.viewer.Option;
import refs.com.hiklife.svc.viewer.RelativeMouseEventListener;
import refs.com.hiklife.svc.viewer.ViewerSample;
/*     */ 
/*     */ 
/*     */ 
/*     */ public class RelativeMouseEventListener
/*     */   implements NativeMouseListener
/*     */ {
/*  13 */   private static final Logger log = LoggerFactory.getLogger(RelativeMouseEventListener.class);
/*     */   
/*     */   private boolean isLeftButtonDown;
/*     */   
/*     */   private boolean isRightButtonDown;
/*     */   
/*     */   private boolean isMiddleButtonDown;
/*     */   private int lastX;
/*     */   private int lastY;
/*     */   private final ViewerSample viewerSample;
/*     */   
/*     */   public RelativeMouseEventListener(ViewerSample viewerSample, int lastX, int lastY) {
/*  25 */     this.viewerSample = viewerSample;
/*  26 */     this.lastX = lastX;
/*  27 */     this.lastY = lastY;
/*     */   }
/*     */ 
/*     */   
/*     */   public void onRelativePointEvent(int dx, int dy, int mask, int wheelData) {
/*  32 */     this.lastX += (int)(dx * Option.instance.getMouseSensitivity());
/*  33 */     this.lastY += (int)(dy * Option.instance.getMouseSensitivity());
/*  34 */     this.lastX = Math.max(this.lastX, 0);
/*  35 */     this.lastY = Math.max(this.lastY, 0);
/*  36 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(this.lastX, this.lastY, mask, wheelData));
/*     */   }
/*     */   private void handleMouseEvent(int x, int y, int mask, int wheelData) {
/*  39 */     int buttonMask = 0;
/*  40 */     int wheelMask = 0;
/*  41 */     if ((mask & 0x2) != 0) {
/*  42 */       this.isLeftButtonDown = false;
/*     */     }
/*  44 */     if ((mask & 0x8) != 0) {
/*  45 */       this.isRightButtonDown = false;
/*     */     }
/*  47 */     if ((mask & 0x20) != 0) {
/*  48 */       this.isMiddleButtonDown = false;
/*     */     }
/*     */ 
/*     */     
/*  52 */     if ((mask & 0x1) != 0 || this.isLeftButtonDown) {
/*  53 */       this.isLeftButtonDown = true;
/*  54 */       buttonMask |= 0x1;
/*     */     } 
/*     */     
/*  57 */     if ((mask & 0x4) != 0 || this.isRightButtonDown) {
/*  58 */       this.isRightButtonDown = true;
/*  59 */       buttonMask |= 0x4;
/*     */     } 
/*     */     
/*  62 */     if ((mask & 0x10) != 0 || this.isMiddleButtonDown) {
/*  63 */       this.isMiddleButtonDown = true;
/*  64 */       buttonMask |= 0x2;
/*     */     } 
/*     */     
/*  67 */     if ((mask & 0x400) != 0) {
/*  68 */       log.trace("Vertical wheel: {}(lines: {})", Integer.valueOf(wheelData), Integer.valueOf(wheelData / 120));
/*  69 */       int clicks = wheelData / 120;
/*  70 */       if (clicks < 0) {
/*     */         
/*  72 */         wheelMask |= 0x8;
/*     */       } else {
/*     */         
/*  75 */         wheelMask |= 0x10;
/*  76 */       }  for (int i = 0; i < Math.abs(clicks); i++) {
/*  77 */         sendPointEvent(x, y, buttonMask | wheelMask);
/*     */       }
/*     */     } 
/*  80 */     sendPointEvent(x, y, buttonMask);
/*     */   }
/*     */   private void sendPointEvent(int x, int y, int buttonMask) {
/*  83 */     int sx = (this.viewerSample.scaleX == 1.0D) ? x : (int)Math.floor(x / this.viewerSample.scaleX);
/*  84 */     int sy = (this.viewerSample.scaleY == 1.0D) ? y : (int)Math.floor(y / this.viewerSample.scaleY);
/*  85 */     Point pos = new Point(sx, sy);
/*  86 */     if (Option.instance.getEnableImageScale() == 0) {
/*  87 */       pos.setLocation(sx + this.viewerSample.offsetX, sy + this.viewerSample.offsetY);
/*     */     }
/*  89 */     this.viewerSample.writeMouseEvent(pos, buttonMask);
/*     */   }
/*     */   
/*     */   class HandleMouse implements Runnable {
/*     */     private final int dx;
/*     */     private final int dy;
/*     */     private final int mask;
/*     */     private final int wheelData;
/*     */     
/*     */     HandleMouse(int dx, int dy, int mask, int wheelData) {
/*  99 */       this.dx = dx;
/* 100 */       this.dy = dy;
/* 101 */       this.mask = mask;
/* 102 */       this.wheelData = wheelData;
/*     */     }
/*     */ 
/*     */     
/*     */     public void run() {
/* 107 */       RelativeMouseEventListener.this.handleMouseEvent(this.dx, this.dy, this.mask, this.wheelData);
/*     */     }
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/RelativeMouseEventListener.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */