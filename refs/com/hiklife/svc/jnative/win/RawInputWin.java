/*     */ package com.hiklife.svc.jnative.win;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeMouseListener;
import refs.com.hiklife.svc.jnative.win.RawInputWin;
import refs.com.hiklife.svc.jnative.win.User32Ext;
import refs.com.sun.jna.Callback;
import refs.com.sun.jna.Memory;
import refs.com.sun.jna.Pointer;
import refs.com.sun.jna.platform.win32.Kernel32;
import refs.com.sun.jna.platform.win32.Kernel32Util;
import refs.com.sun.jna.platform.win32.User32;
import refs.com.sun.jna.platform.win32.User32Util;
import refs.com.sun.jna.platform.win32.WinDef;
import refs.com.sun.jna.platform.win32.WinUser;
import refs.com.sun.jna.ptr.IntByReference;
/*     */ 
/*     */ public class RawInputWin {
/*  18 */   private static final Logger log = LoggerFactory.getLogger(RawInputWin.class);
/*     */   
/*     */   private static final int WS_EX_TOOLWINDOW = 128;
/*     */   
/*     */   private static final int WS_EX_NOACTIVATE = 128;
/*     */   
/*     */   private static final int RIDEV_REMOVE = 1;
/*     */   
/*     */   private static final int RIDEV_INPUTSINK = 256;
/*     */   
/*     */   private static final int WM_INPUT = 255;
/*     */   
/*     */   private static final int RID_INPUT = 268435459;
/*     */   
/*     */   private static final int RIM_TYPEMOUSE = 0;
/*     */   
/*     */   private WinDef.HWND hwnd;
/*     */   
/*     */   private boolean isRunning;
/*     */   
/*     */   private NativeMouseListener listener;
/*     */ 
/*     */   
/*     */   private RawInputWin() {}
/*     */   
/*     */   private static class RawInputWinHolder
/*     */   {
/*  45 */     private static final RawInputWin instance = new RawInputWin(); }
/*     */   
/*     */   public static RawInputWin instance() {
/*  48 */     return RawInputWinHolder.instance;
/*     */   }
/*     */   
/*     */   public void setListener(NativeMouseListener listener) {
/*  52 */     this.listener = listener;
/*     */   }
/*     */   
/*     */   public void openInput() {
/*  56 */     if (!this.isRunning) {
/*  57 */       this.isRunning = true;
/*  58 */       (new Thread(this::createWindow)).start();
/*     */     } else {
/*  60 */       registerInputDevice(this.hwnd);
/*     */     } 
/*     */   }
/*     */   public void releaseWindow() {
/*  64 */     log.debug("Release Window");
/*  65 */     registerInputDevice(null);
/*     */   }
/*     */   
/*     */   private void createWindow() {
/*  69 */     String wndClassName = "RawInputSinkClass";
/*  70 */     String wndTitle = "Raw Input Sink";
/*     */     
/*  72 */     WinUser.WNDCLASSEX wndClassEx = new WinUser.WNDCLASSEX();
/*  73 */     wndClassEx.lpfnWndProc = new WindowProc();
/*  74 */     wndClassEx.cbClsExtra = 0;
/*  75 */     wndClassEx.cbWndExtra = 0;
/*  76 */     wndClassEx.style = 3;
/*  77 */     wndClassEx.lpszClassName = wndClassName;
/*     */     
/*  79 */     if (User32.INSTANCE.RegisterClassEx(wndClassEx).intValue() == 0) {
/*  80 */       System.err.println("register window failed!");
/*  81 */       System.err.println("" + Kernel32.INSTANCE.GetLastError() + "\n" + Kernel32Util.getLastErrorMessage());
/*     */       return;
/*     */     } 
/*  84 */     this.hwnd = User32Util.createWindowEx(128, wndClassName, wndTitle, 0, 1, 1, 100, 100, null, null, null, null);
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
/*  96 */     if (this.hwnd == null) {
/*  97 */       log.error("Create window failed!");
/*  98 */       log.error("{}\n{}", Integer.valueOf(Kernel32.INSTANCE.GetLastError()), Kernel32Util.getLastErrorMessage());
/*     */       return;
/*     */     } 
/* 101 */     registerInputDevice(this.hwnd);
/*     */ 
/*     */     
/* 104 */     WinUser.MSG msg = new WinUser.MSG();
/* 105 */     while (this.hwnd != null && User32.INSTANCE.GetMessage(msg, this.hwnd, 0, 0) != 0) {
/* 106 */       User32.INSTANCE.TranslateMessage(msg);
/* 107 */       User32.INSTANCE.DispatchMessage(msg);
/*     */     } 
/* 109 */     log.info("RawInputWin end");
/*     */   }
/*     */   
/*     */   private void registerInputDevice(WinDef.HWND hwnd) {
/* 113 */     User32Ext.RAWINPUTDEVICE[] devices = new User32Ext.RAWINPUTDEVICE[1];
/* 114 */     User32Ext.RAWINPUTDEVICE device = new User32Ext.RAWINPUTDEVICE();
/*     */     
/* 116 */     device.usUsagePage = new WinDef.USHORT(1L);
/*     */     
/* 118 */     device.usUsage = new WinDef.USHORT(2L);
/*     */ 
/*     */     
/* 121 */     device.dwFlags = new WinDef.DWORD(256L);
/* 122 */     device.hwndTarget = hwnd;
/* 123 */     if (hwnd == null) {
/* 124 */       device.dwFlags = new WinDef.DWORD(1L);
/*     */     }
/* 126 */     devices[0] = device;
/* 127 */     boolean success = User32Ext.INSTANCE.RegisterRawInputDevices(devices, new WinDef.UINT(devices.length), new WinDef.UINT(device
/*     */ 
/*     */           
/* 130 */           .size()));
/*     */     
/* 132 */     if (!success) {
/* 133 */       int error = Kernel32.INSTANCE.GetLastError();
/* 134 */       System.err.println("RegisterRawInputDevices failed: " + error);
/*     */     }  } class WindowProc implements Callback { public WinDef.LRESULT callback(WinDef.HWND hwnd, WinDef.UINT uMsg, WinDef.WPARAM wParam, WinDef.LPARAM lParam) { Pointer hRawInput; int headerSize; IntByReference sizeRef;
/*     */       int result;
/*     */       int dwSize;
/*     */       Memory buffer;
/*     */       User32Ext.RAWINPUT raw;
/* 140 */       switch (uMsg.intValue()) {
/*     */         case 2:
/*     */         case 16:
/* 143 */           RawInputWin.this.releaseWindow();
/*     */           break;
/*     */         case 255:
/* 146 */           hRawInput = new Pointer(lParam.longValue());
/* 147 */           headerSize = (new User32Ext.RAWINPUTHEADER()).size();
/*     */           
/* 149 */           sizeRef = new IntByReference(0);
/* 150 */           result = User32Ext.INSTANCE.GetRawInputData(hRawInput, 268435459, null, sizeRef, headerSize);
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */           
/* 157 */           if (result == -1) {
/* 158 */             RawInputWin.log.error("GetRawInputData failed (query size)");
/*     */             break;
/*     */           } 
/* 161 */           dwSize = sizeRef.getValue();
/* 162 */           if (dwSize <= headerSize) {
/* 163 */             RawInputWin.log.error("Invalid raw input size: {}", Integer.valueOf(dwSize));
/*     */             break;
/*     */           } 
/* 166 */           buffer = new Memory(dwSize);
/*     */           
/* 168 */           result = User32Ext.INSTANCE.GetRawInputData(hRawInput, 268435459, (Pointer)buffer, sizeRef, headerSize);
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */           
/* 175 */           if (result == -1) {
/* 176 */             RawInputWin.log.error("GetRawInputData failed (read data)");
/*     */             
/*     */             break;
/*     */           } 
/* 180 */           raw = new User32Ext.RAWINPUT((Pointer)buffer);
/* 181 */           raw.read();
/* 182 */           if (raw.header.dwType == 0) {
/* 183 */             raw.read();
/* 184 */             if (raw.mouse.usFlags.intValue() == 0) {
/* 185 */               handleMouseRow(raw.mouse);
/*     */             }
/*     */           } 
/*     */           break;
/*     */       } 
/* 190 */       return User32.INSTANCE.DefWindowProc(hwnd, uMsg.intValue(), wParam, lParam); }
/*     */ 
/*     */     
/*     */     private void handleMouseRow(User32Ext.RAWMOUSE rawMouse) {
/* 194 */       short buttonFlags = rawMouse.getButtonFlags();
/* 195 */       sendNativeMouseEvent(buttonFlags, rawMouse.lLastX.intValue(), rawMouse.lLastY.intValue(), rawMouse.getButtonData());
/*     */     }
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
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     private void sendNativeMouseEvent(short mask, int dx, int dy, int wheelData) {
/* 238 */       if (RawInputWin.this.listener != null)
/* 239 */         RawInputWin.this.listener.onRelativePointEvent(dx, dy, mask, wheelData); 
/*     */     } }
/*     */ 
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/win/RawInputWin.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */