/*
 * Bounded replay of the C99 sources generated from NASA Ogma's public
 * Doorstop demonstration by research run #44023167656.
 *
 * Compile independently against official/generated/monitor.c and against
 * int16/generated/monitor.c, defining USE_INT16 only for the latter.
 * This tests the generated C behavior on sample inputs, not real flight code.
 */
#include <stdint.h>
#include <stdio.h>
#include "monitor.h"

#ifdef USE_INT16
int16_t temperature = 0;
#else
int8_t temperature = 0;
#endif

static int upper_violations = 0;
static int lower_violations = 0;

void handlerREQ001(void) { upper_violations++; }
void handlerREQ002(void) { lower_violations++; }

int main(void) {
  int disagreements = 0;
  int accepted_disagreements = 0;
  int accepted = 0;
#ifdef USE_INT16
  const int last = 181;
#else
  const int last = 127;
#endif

  for (int x = -128; x <= last; ++x) {
    temperature = x;
    upper_violations = 0;
    lower_violations = 0;
    step();

    const int expected_upper = x > 180;
    const int expected_lower = x < 120;
    const int intended_accept = !expected_upper && !expected_lower;
    const int actual_accept = !upper_violations && !lower_violations;
    if (intended_accept) accepted++;
    if (upper_violations != expected_upper || lower_violations != expected_lower) {
      disagreements++;
      if (intended_accept) accepted_disagreements++;
    }
    if (x == 120) {
      printf("boundary input=120 upper=%d lower=%d intended_accept=%d actual_accept=%d\n",
             upper_violations, lower_violations, intended_accept, actual_accept);
#ifdef USE_INT16
      if (!actual_accept) return 11;
#else
      if (actual_accept || upper_violations != 1 || lower_violations != 0) return 12;
#endif
    }
  }

  printf("intended_accept_count=%d total_disagreements=%d accepted_disagreements=%d\n",
         accepted, disagreements, accepted_disagreements);
#ifdef USE_INT16
  if (accepted != 61 || disagreements != 0 || accepted_disagreements != 0) return 21;
  puts("PASS: generated Int16 monitor preserves numeric thresholds on replayed range");
#else
  if (accepted != 8 || disagreements != 203 || accepted_disagreements != 8) return 22;
  puts("PASS: generated Int8 monitor disagrees on 203 values including all 8 accepted values");
#endif
  return 0;
}
