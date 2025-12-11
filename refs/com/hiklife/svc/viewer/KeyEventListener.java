/*     */ package com.hiklife.svc.viewer;
/*     */ 
/*     */ import java.awt.event.FocusEvent;
/*     */ import java.awt.event.KeyEvent;
/*     */ import java.awt.event.KeyListener;
/*     */ import java.util.ArrayList;
/*     */ import java.util.HashSet;
/*     */ import java.util.List;
/*     */ import java.util.Set;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.viewer.KeyEventListener;
import refs.com.hiklife.svc.viewer.KeyMouseEventThreadPool;
import refs.com.hiklife.svc.viewer.VK;
import refs.com.hiklife.svc.viewer.ViewerSample;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class KeyEventListener
/*     */   implements KeyListener
/*     */ {
/*  22 */   private static final Logger log = LoggerFactory.getLogger(KeyEventListener.class);
/*     */ 
/*     */   
/*     */   private final ViewerSample viewerSample;
/*     */ 
/*     */   
/*  28 */   private final Set<KeyPressedEvent> pressedKeys = new HashSet<>();
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   KeyEventListener(ViewerSample viewerSample) {
/*  37 */     this.viewerSample = viewerSample;
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
/*     */   private synchronized void processLocalKeyEvent(KeyEvent keyEvent) {
/*  49 */     log.debug("KeyCode:{}", Integer.valueOf(keyEvent.getKeyCode()));
/*  50 */     int xkCode = VK.vkToXk(keyEvent.getKeyCode(), keyEvent.getKeyLocation());
/*  51 */     this.viewerSample.writeKeyEvent(xkCode, (keyEvent.getID() == 401) ? 1 : 0);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void keyTyped(KeyEvent e) {
/*  62 */     e.consume();
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
/*     */   public void keyPressed(KeyEvent e) {
/*  75 */     log.debug("keyPressed, {}", Integer.valueOf(e.getKeyCode()));
/*  76 */     KeyMouseEventThreadPool.getInstance().execute(new HandleLocalKey(e));
/*  77 */     this.pressedKeys.add(new KeyPressedEvent(e));
/*  78 */     log.debug("keyPressed:supplement,add:{}", Integer.valueOf(e.getKeyCode()));
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
/*     */   public void keyReleased(KeyEvent e) {
/*  90 */     log.debug("keyReleased, {}", Integer.valueOf(e.getKeyCode()));
/*  91 */     KeyMouseEventThreadPool.getInstance().execute(new HandleLocalKey(e));
/*  92 */     this.pressedKeys.remove(new KeyPressedEvent(e));
/*  93 */     log.debug("keyReleased:supplement,remove:{}", Integer.valueOf(e.getKeyCode()));
/*     */   }
/*     */ 
/*     */   
/*     */   class HandleLocalKey
/*     */     implements Runnable
/*     */   {
/*     */     private KeyEvent e;
/*     */ 
/*     */     
/*     */     HandleLocalKey(KeyEvent e) {
/* 104 */       this.e = e;
/*     */     }
/*     */ 
/*     */     
/*     */     public void run() {
/* 109 */       KeyEventListener.this.processLocalKeyEvent(this.e);
/*     */     }
/*     */   }
/*     */ 
/*     */   
/*     */   public static class KeyPressedEvent
/*     */   {
/*     */     int modifiers;
/*     */     
/*     */     int keyCode;
/*     */     
/*     */     char keyChar;
/*     */     int keyLocation;
/*     */     long when;
/*     */     
/*     */     KeyPressedEvent(int modifiers, int keyCode, char keyChar, int keyLocation, long when) {
/* 125 */       this.keyChar = keyChar;
/* 126 */       this.keyCode = keyCode;
/* 127 */       this.modifiers = modifiers;
/* 128 */       this.keyLocation = keyLocation;
/* 129 */       this.when = when;
/*     */     }
/*     */     KeyPressedEvent(KeyEvent e) {
/* 132 */       this(e.getModifiers(), e.getKeyCode(), e.getKeyChar(), e.getKeyLocation(), e.getWhen());
/*     */     }
/*     */ 
/*     */     
/*     */     public boolean equals(Object obj) {
/* 137 */       if (this == obj) {
/* 138 */         return true;
/*     */       }
/* 140 */       if (obj == null) {
/* 141 */         return false;
/*     */       }
/* 143 */       if (obj instanceof KeyPressedEvent) {
/* 144 */         KeyPressedEvent other = (KeyPressedEvent)obj;
/* 145 */         if (this.keyCode == other.keyCode) {
/* 146 */           return true;
/*     */         }
/*     */       } 
/* 149 */       return false;
/*     */     }
/*     */ 
/*     */     
/*     */     public int hashCode() {
/* 154 */       return this.keyCode;
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
/*     */   public void focusLost(FocusEvent e) {
/* 167 */     log.debug("focusLost:pressedKeys,size:{}", Integer.valueOf(this.pressedKeys.size()));
/* 168 */     List<KeyEvent> sendList = new ArrayList<>();
/* 169 */     for (KeyPressedEvent pressedKey : this.pressedKeys) {
/*     */       
/* 171 */       KeyEvent keyEvent = new KeyEvent(e.getComponent(), 402, pressedKey.when, pressedKey.modifiers, pressedKey.keyCode, pressedKey.keyChar, pressedKey.keyLocation);
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */       
/* 178 */       sendList.add(keyEvent);
/*     */     } 
/* 180 */     for (KeyEvent keyEvent : sendList) {
/* 181 */       log.debug("focusLost:supplement {}", Integer.valueOf(keyEvent.getKeyCode()));
/* 182 */       keyReleased(keyEvent);
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/KeyEventListener.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */