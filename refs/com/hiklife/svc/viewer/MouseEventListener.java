/*     */ package com.hiklife.svc.viewer;
/*     */ 
/*     */ import java.awt.Point;
/*     */ import java.awt.event.MouseEvent;
/*     */ import java.awt.event.MouseListener;
/*     */ import java.awt.event.MouseMotionListener;
/*     */ import java.awt.event.MouseWheelEvent;
/*     */ import java.awt.event.MouseWheelListener;

import refs.com.hiklife.svc.viewer.KeyMouseEventThreadPool;
import refs.com.hiklife.svc.viewer.MouseEventListener;
import refs.com.hiklife.svc.viewer.Option;
import refs.com.hiklife.svc.viewer.ViewerSample;
/*     */ 
/*     */ public class MouseEventListener
/*     */   implements MouseListener, MouseMotionListener, MouseWheelListener
/*     */ {
/*     */   private final ViewerSample viewerSample;
/*     */   
/*     */   MouseEventListener(ViewerSample viewerSample) {
/*  16 */     this.viewerSample = viewerSample;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void handleMouseEvent(MouseEvent e) {
/*     */     int buttonMask;
/*  27 */     switch (e.getID()) {
/*     */       case 501:
/*     */       case 502:
/*     */       case 503:
/*     */       case 506:
/*     */       case 507:
/*  33 */         buttonMask = 0;
/*  34 */         if ((e.getModifiersEx() & 0x400) != 0) {
/*  35 */           buttonMask |= 0x1;
/*     */         }
/*  37 */         if ((e.getModifiersEx() & 0x800) != 0) {
/*  38 */           buttonMask |= 0x2;
/*     */         }
/*  40 */         if ((e.getModifiersEx() & 0x1000) != 0) {
/*  41 */           buttonMask |= 0x4;
/*     */         }
/*  43 */         if (e.getID() == 507) {
/*  44 */           int wheelMask = 0;
/*  45 */           int clicks = ((MouseWheelEvent)e).getWheelRotation();
/*  46 */           if (clicks < 0) {
/*  47 */             wheelMask |= e.isShiftDown() ? 32 : 8;
/*     */           } else {
/*  49 */             wheelMask |= e.isShiftDown() ? 64 : 16;
/*  50 */           }  Point pt = new Point(e.getX(), e.getY());
/*  51 */           for (int i = 0; i < Math.abs(clicks); i++) {
/*  52 */             sendPointEvent(pt, buttonMask | wheelMask);
/*  53 */             sendPointEvent(pt, buttonMask);
/*     */           } 
/*  55 */           sendPointEvent(new Point(e.getX(), e.getY()), buttonMask);
/*     */           break;
/*     */         } 
/*  58 */         sendPointEvent(new Point(e.getX(), e.getY()), buttonMask);
/*     */         break;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void sendPointEvent(Point pos, int buttonMask) {
/*  75 */     (this.viewerSample.getLastPoint()).x = pos.x;
/*  76 */     (this.viewerSample.getLastPoint()).y = pos.y;
/*  77 */     int sx = (this.viewerSample.scaleX == 1.0D) ? pos.x : (int)Math.floor(pos.x / this.viewerSample.scaleX);
/*  78 */     int sy = (this.viewerSample.scaleY == 1.0D) ? pos.y : (int)Math.floor(pos.y / this.viewerSample.scaleY);
/*  79 */     pos.setLocation(sx, sy);
/*  80 */     if (Option.instance.getEnableImageScale() == 0)
/*     */     {
/*  82 */       pos.setLocation(sx + this.viewerSample.offsetX, sy + this.viewerSample.offsetY);
/*     */     }
/*     */     
/*  85 */     this.viewerSample.writeMouseEvent(pos, buttonMask);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseClicked(MouseEvent evt) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mousePressed(MouseEvent evt) {
/* 108 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(evt));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseReleased(MouseEvent evt) {
/* 118 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(evt));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseEntered(MouseEvent evt) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseExited(MouseEvent evt) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseDragged(MouseEvent evt) {
/* 148 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(evt));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseMoved(MouseEvent evt) {
/* 158 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(evt));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void mouseWheelMoved(MouseWheelEvent evt) {
/* 168 */     KeyMouseEventThreadPool.getInstance().execute(new HandleMouse(evt));
/*     */   }
/*     */ 
/*     */   
/*     */   class HandleMouse
/*     */     implements Runnable
/*     */   {
/*     */     private MouseEvent e;
/*     */     
/*     */     HandleMouse(MouseEvent e) {
/* 178 */       this.e = e;
/*     */     }
/*     */ 
/*     */     
/*     */     public void run() {
/* 183 */       MouseEventListener.this.handleMouseEvent(this.e);
/*     */     }
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/MouseEventListener.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */