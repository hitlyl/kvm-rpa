package com.hiklife.svc.core.protocol.security;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;

public interface Auth {
  byte[] encrypt() throws InvalidRFBMessageException;
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/Auth.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */