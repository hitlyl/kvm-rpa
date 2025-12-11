/*     */ package com.hiklife.svc.jnative.linux;
/*     */ import java.io.IOException;
/*     */ import java.util.ArrayList;
/*     */ import java.util.Iterator;
/*     */ import java.util.List;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeMouseListener;
import refs.com.hiklife.svc.jnative.linux.LibCExt;
import refs.com.hiklife.svc.jnative.linux.MouseFinder;
import refs.com.hiklife.svc.jnative.linux.RawInputLinux;
import refs.com.sun.jna.Memory;
import refs.com.sun.jna.Pointer;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class RawInputLinux
/*     */ {
/*  18 */   private static final Logger log = LoggerFactory.getLogger(RawInputLinux.class);
/*     */   
/*     */   private boolean isRunning = false;
/*     */   
/*     */   private List<Integer> fds;
/*     */   
/*     */   private static final int EV_SYN = 0;
/*     */   private static final int EV_KEY = 1;
/*     */   private static final int EV_REL = 2;
/*     */   private static final int SYN_REPORT = 0;
/*     */   private static final int BTN_LEFT = 272;
/*     */   private static final int BTN_RIGHT = 273;
/*     */   private static final int BTN_MIDDLE = 274;
/*     */   private static final int REL_X = 0;
/*     */   private static final int REL_Y = 1;
/*     */   private static final int REL_WHEEL = 8;
/*     */   private NativeMouseListener listener;
/*     */   private int dx;
/*     */   private int dy;
/*     */   private int mask;
/*     */   private int wheelData;
/*     */   
/*     */   private static class RawInputLinuxHolder
/*     */   {
/*  42 */     private static final RawInputLinux instance = new RawInputLinux(); }
/*     */   
/*     */   public static RawInputLinux instance() {
/*  45 */     return RawInputLinuxHolder.instance;
/*     */   }
/*     */   
/*     */   public void setListener(NativeMouseListener listener) {
/*  49 */     this.listener = listener;
/*     */   }
/*     */ 
/*     */   
/*     */   public int openInput() {
/*  54 */     if (!this.isRunning) {
/*  55 */       List<String> mousePaths; this.fds = new ArrayList<>();
/*     */       
/*     */       try {
/*  58 */         mousePaths = MouseFinder.findMouseEventPaths();
/*  59 */       } catch (IOException e) {
/*  60 */         log.error("FindMouseEventPaths error", e);
/*  61 */         return -2;
/*     */       } 
/*  63 */       if (mousePaths.isEmpty()) {
/*  64 */         log.error("No mouse devices were detected.");
/*  65 */         return -2;
/*     */       } 
/*  67 */       for (String path : mousePaths) {
/*  68 */         int fd = LibCExt.INSTANCE.open(path, 0);
/*  69 */         if (fd < 0) {
/*  70 */           log.error("Insufficient permissions to access input device");
/*     */           
/*  72 */           release();
/*  73 */           return -1;
/*     */         } 
/*     */         
/*  76 */         int result = LibCExt.INSTANCE.ioctl(fd, 1074021776L, new Object[] { Integer.valueOf(1) });
/*  77 */         if (result < 0) {
/*  78 */           log.error("Insufficient permissions to grab device");
/*     */           
/*  80 */           release();
/*  81 */           return -1;
/*     */         } 
/*  83 */         this.fds.add(Integer.valueOf(fd));
/*  84 */         this.isRunning = true;
/*     */       } 
/*  86 */       for (Iterator<Integer> iterator = this.fds.iterator(); iterator.hasNext(); ) { int fd = ((Integer)iterator.next()).intValue();
/*  87 */         (new Thread(() -> {
/*     */               Memory buffer = new Memory(24L); while (this.isRunning) {
/*     */                 int n = LibCExt.INSTANCE.read(fd, (Pointer)buffer, 24); if (n == 24) {
/*     */                   int type = buffer.getShort(16L); int code = buffer.getShort(18L); int value = buffer.getInt(20L); if (type == 2 && code == 0) {
/*     */                     this.dx = value; this.mask = 0; this.wheelData = 0;
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 2 && code == 1) {
/*     */                     this.dy = value;
/*     */                     this.mask = 0;
/*     */                     this.wheelData = 0;
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 2 && code == 8) {
/*     */                     this.dx = 0;
/*     */                     this.dy = 0;
/*     */                     this.wheelData = value * 120;
/*     */                     this.mask = 1024;
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 1 && code == 272) {
/*     */                     this.mask = (value == 1) ? 1 : ((value == 0) ? 2 : this.mask);
/*     */                     this.dx = 0;
/*     */                     this.dy = 0;
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 1 && code == 273) {
/*     */                     this.dx = 0;
/*     */                     this.dy = 0;
/*     */                     this.mask = (value == 1) ? 4 : ((value == 0) ? 8 : this.mask);
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 1 && code == 274) {
/*     */                     this.dx = 0;
/*     */                     this.dy = 0;
/*     */                     this.mask = (value == 1) ? 16 : ((value == 0) ? 32 : this.mask);
/*     */                     continue;
/*     */                   } 
/*     */                   if (type == 0 && code == 0 && this.listener != null)
/*     */                     this.listener.onRelativePointEvent(this.dx, this.dy, this.mask, this.wheelData); 
/*     */                 } 
/*     */               } 
/* 129 */             })).start(); }
/*     */     
/*     */     } 
/* 132 */     return 0;
/*     */   }
/*     */   
/*     */   public void release() {
/* 136 */     this.isRunning = false;
/* 137 */     if (this.fds != null) {
/* 138 */       for (Iterator<Integer> iterator = this.fds.iterator(); iterator.hasNext(); ) { int fd = ((Integer)iterator.next()).intValue();
/* 139 */         LibCExt.INSTANCE.ioctl(fd, 1074021776L, new Object[] { Integer.valueOf(0) });
/* 140 */         LibCExt.INSTANCE.close(fd); }
/*     */       
/* 142 */       this.fds = null;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void main(String[] args) throws Exception {
/* 152 */     RawInputLinux clipper = new RawInputLinux();
/*     */     
/* 154 */     clipper.openInput();
/*     */ 
/*     */     
/* 157 */     long delay = 0L;
/* 158 */     while (delay < 10000L) {
/*     */       try {
/* 160 */         Thread.sleep(1000L);
/* 161 */         delay += 1000L;
/* 162 */       } catch (InterruptedException ex) {
/*     */         break;
/*     */       } 
/*     */     } 
/*     */ 
/*     */     
/* 168 */     clipper.release();
/*     */   }
/*     */   
/*     */   private RawInputLinux() {}
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/linux/RawInputLinux.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */