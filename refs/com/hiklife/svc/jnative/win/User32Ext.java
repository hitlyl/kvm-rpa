/*     */ package com.hiklife.svc.jnative.win;
import refs.com.hiklife.svc.jnative.win.User32Ext;
import refs.com.sun.jna.Native;
import refs.com.sun.jna.Pointer;
import refs.com.sun.jna.Structure;
import refs.com.sun.jna.Structure.FieldOrder;
import refs.com.sun.jna.platform.win32.WinDef;
import refs.com.sun.jna.ptr.IntByReference;
import refs.com.sun.jna.win32.StdCallLibrary;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public interface User32Ext
/*     */   extends StdCallLibrary
/*     */ {
/*  18 */   public static final User32Ext INSTANCE = (User32Ext)Native.load("user32", User32Ext.class);
/*     */ 
/*     */   
/*     */   boolean ClipCursor(RECT.ByReference paramByReference);
/*     */ 
/*     */   
/*     */   short GetKeyState(int paramInt);
/*     */ 
/*     */   
/*     */   boolean RegisterRawInputDevices(RAWINPUTDEVICE[] paramArrayOfRAWINPUTDEVICE, WinDef.UINT paramUINT1, WinDef.UINT paramUINT2);
/*     */ 
/*     */   
/*     */   int GetRawInputData(Pointer paramPointer1, int paramInt1, Pointer paramPointer2, IntByReference paramIntByReference, int paramInt2);
/*     */ 
/*     */   
/*     */   @FieldOrder({"left", "top", "right", "bottom"})
/*     */   public static class RECT
/*     */     extends Structure
/*     */   {
/*     */     public int left;
/*     */     
/*     */     public int top;
/*     */     
/*     */     public int right;
/*     */     
/*     */     public int bottom;
/*     */     
/*     */     public static class ByReference
/*     */       extends RECT
/*     */       implements Structure.ByReference {}
/*     */   }
/*     */   
/*     */   public static class ByReference
/*     */     extends RECT
/*     */     implements Structure.ByReference {}
/*     */   
/*     */   @FieldOrder({"usUsagePage", "usUsage", "dwFlags", "hwndTarget"})
/*     */   public static class RAWINPUTDEVICE
/*     */     extends Structure
/*     */   {
/*     */     public WinDef.USHORT usUsagePage;
/*     */     public WinDef.USHORT usUsage;
/*     */     public WinDef.DWORD dwFlags;
/*     */     public WinDef.HWND hwndTarget;
/*     */   }
/*     */   
/*     */   @FieldOrder({"dwType", "dwSize", "hDevice", "wParam"})
/*     */   public static class RAWINPUTHEADER
/*     */     extends Structure
/*     */   {
/*     */     public int dwType;
/*     */     public int dwSize;
/*     */     public Pointer hDevice;
/*     */     public WinDef.LPARAM wParam;
/*     */   }
/*     */   
/*     */   @FieldOrder({"usFlags", "ulButtons", "ulRawButtons", "lLastX", "lLastY", "ulExtraInformation"})
/*     */   public static class RAWMOUSE
/*     */     extends Structure
/*     */   {
/*     */     public WinDef.USHORT usFlags;
/*     */     public WinDef.ULONG ulButtons;
/*     */     public WinDef.ULONG ulRawButtons;
/*     */     public WinDef.LONG lLastX;
/*     */     public WinDef.LONG lLastY;
/*     */     public WinDef.ULONG ulExtraInformation;
/*     */     
/*     */     public short getButtonFlags() {
/*  86 */       return this.ulButtons.shortValue();
/*     */     }
/*     */     
/*     */     public short getButtonData() {
/*  90 */       return (short)(this.ulButtons.intValue() >>> 16 & 0xFFFF);
/*     */     }
/*     */   }
/*     */   
/*     */   @FieldOrder({"header", "mouse"})
/*     */   public static class RAWINPUT
/*     */     extends Structure {
/*     */     public User32Ext.RAWINPUTHEADER header;
/*     */     
/*     */     public RAWINPUT(Pointer p) {
/* 100 */       super(p);
/*     */     }
/*     */     
/*     */     public User32Ext.RAWMOUSE mouse;
/*     */     
/*     */     public RAWINPUT() {}
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/win/User32Ext.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */