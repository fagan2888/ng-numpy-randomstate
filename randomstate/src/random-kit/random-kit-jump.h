#pragma once
#include "random-kit.h"
#include <stdlib.h>

/* parameters for computing Jump */
#define W_SIZE 32 /* size of unsigned long */
#define MEXP 19937
#define P_SIZE ((MEXP/W_SIZE)+1)
#define LSB 0x00000001UL
#define QQ 7
#define LL 128  /* LL = 2^(QQ) */


void randomkit_jump(randomkit_state * state, const char * jump_str);

void set_coef(unsigned long *pf, unsigned int deg, unsigned long v);