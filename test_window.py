import viser
import time

def main():
    server = viser.ViserServer()
    
    @server.on_client_connect
    def _(client: viser.ClientHandle) -> None:
        # Create a modal window
        # with client.gui.add_modal("Settings Window"):
        #     # Add markdown content
        #     client.gui.add_markdown("### Configure Settings")
            
        #     # Add input controls
        #     name_input = client.gui.add_text("Name", initial_value="User")
        #     value_slider = client.gui.add_slider("Value", min=0, max=100, initial_value=50)
        #     color_picker = client.gui.add_rgb("Color", initial_value=(255, 0, 0))
        #     checkbox = client.gui.add_checkbox("Enable Feature", initial_value=True)
            
        #     # Add buttons
        #     save_button = client.gui.add_button("Save")
        #     cancel_button = client.gui.add_button("Cancel")
            
        #     @save_button.on_click
        #     def _(_):
        #         print(f"Saved: {name_input.value}, {value_slider.value}")
            
        #     @cancel_button.on_click
        #     def _(_):
        #         print("Cancelled")
        
        with client.gui.add_modal("My Window Title"):
            # Add content inside the modal
            client.gui.add_markdown("**Welcome to my window!**")
    
    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    main()