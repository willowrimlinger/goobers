#define DISPLAY_PRINTF(format, args...) sprintf(buf, format, ##args); \
gfx->print(buf);
