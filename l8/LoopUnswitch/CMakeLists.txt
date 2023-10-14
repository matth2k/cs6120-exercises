add_llvm_pass_plugin(LoopUnswitchPass MODULE
    # List your source files here.
    LoopUnswitch.cpp
    PLUGIN_TOOL
    opt
)
