package com.hiklife.svc.jnative;

import refs.com.hiklife.svc.jnative.NativeMouseListener;

public interface NativeLib {
  int clipCursor(int paramInt1, int paramInt2, int paramInt3, int paramInt4, NativeMouseListener paramNativeMouseListener);
  
  void releaseCursor();
  
  boolean[] getLockKeyState();
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/NativeLib.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */