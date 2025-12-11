package com.hiklife.svc.jnative;

public interface NativeMouseListener {
  public static final short RI_MOUSE_LEFT_BUTTON_DOWN = 1;
  
  public static final short RI_MOUSE_LEFT_BUTTON_UP = 2;
  
  public static final short RI_MOUSE_RIGHT_BUTTON_DOWN = 4;
  
  public static final short RI_MOUSE_RIGHT_BUTTON_UP = 8;
  
  public static final short RI_MOUSE_MIDDLE_BUTTON_DOWN = 16;
  
  public static final short RI_MOUSE_MIDDLE_BUTTON_UP = 32;
  
  public static final short RI_MOUSE_WHEEL = 1024;
  
  void onRelativePointEvent(int paramInt1, int paramInt2, int paramInt3, int paramInt4);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/NativeMouseListener.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */