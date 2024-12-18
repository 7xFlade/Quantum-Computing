import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import logging
from qkd_program import create_two_node_network
from alice_program import AliceProgram
from bob_program import BobProgram
from squidasm.run.stack.run import run
from squidasm.util import create_two_node_network

def run_program(name1, name2, noise, iterations, output_widget, progress_bar, status_label,num_epr):
    try:
        # Clear any existing text from the output display
        output_widget.delete("1.0", tk.END)

        # Convert string inputs to their proper numeric types
        noise = float(noise)
        iterations = int(iterations)

        # Update the UI to show simulation is starting
        status_label.config(text="Running QKD simulation...")
        progress_bar["value"] = 0
        root.update_idletasks()

        # Set up the quantum network with two nodes (Alice and Bob) and specified noise level
        cfg = create_two_node_network(node_names=["Alice", "Bob"], link_noise=noise)

        # Initialize the quantum programs for both parties with specified number of EPR pairs
        alice_program = AliceProgram(num_epr=num_epr)
        bob_program = BobProgram(num_epr=num_epr)

        # Reduce logging verbosity to only show errors
        alice_program.logger.setLevel(logging.ERROR)
        bob_program.logger.setLevel(logging.ERROR)

        # Execute the quantum programs for specified number of iterations
        alice_results, bob_results = run(
            config=cfg, programs={"Alice": alice_program, "Bob": bob_program}, num_times=iterations
        )

        # Process results for each iteration
        for i, (alice_result, bob_result) in enumerate(zip(alice_results, bob_results)):
            # Update progress bar
            progress_bar["value"] = (i + 1) / iterations * 100
            root.update_idletasks()

            output_widget.insert(tk.END, f"Run {i + 1}:\n")

            # Get measurement results from both parties
            alice_pairs_info = alice_result
            bob_pairs_info = bob_result

            # Initialize lists to store the raw key bits
            bob_raw_key = []
            alice_raw_key = []

            # Initialize counters for basis choices
            alice_zcount  = 0
            bob_zcount = 0
            alice_xcount = 0
            bob_xcount = 0

            # Create header for the measurement results table
            output_widget.insert(tk.END, f"BitNum | Same Basis | Same Outcome | {name2}'s Outcome | {name1}'s Outcome | Bob's Basis | Alice's Basis\n")
            
            # Process each pair of measurements
            for alice_pair, bob_pair in zip(alice_pairs_info, bob_pairs_info):
                # Handle potential None values in measurement outcomes
                alice_outcome = alice_pair.test_outcome if alice_pair.test_outcome is not None else "N/A"
                same_outcome = alice_pair.same_outcome if alice_pair.same_outcome is not None else "N/A"
                bob_outcome = bob_pair.outcome if bob_pair.outcome is not None else "N/A"

                # Check if both parties measured same value
                if (alice_pair.outcome == bob_pair.outcome): 
                    same_outcome = "True " 
                else:
                    same_outcome = "False"

                # If same basis was used, add to raw key
                if (alice_pair.same_basis):
                    alice_pair.same_basis = "True "
                    bob_raw_key.append(bob_pair.outcome)
                    alice_raw_key.append(alice_pair.outcome)
                else:
                    alice_pair.same_basis = "False"

                # Convert numeric basis choice to Z/X notation and count occurrences
                if (bob_pair.basis == 0):
                    bob_basis = "Z"
                    bob_zcount += 1
                else:
                    bob_basis = "X"
                    bob_xcount += 1
                if (alice_pair.basis == 0):
                    alice_basis = "Z"
                    alice_zcount += 1
                else:
                    alice_basis = "X"
                    alice_xcount += 1
        
                # Add row to results table
                output_widget.insert(tk.END, f"{alice_pair.index:>6} | {alice_pair.same_basis} | "
                                            f"{same_outcome} | {bob_pair.outcome:>13} | "
                                            f"{alice_pair.outcome:>14} | {bob_basis:>10} | {alice_basis:>12}\n")
            output_widget.insert(tk.END, "\n")

            # Calculate Quantum Bit Error Rate (QBER)
            error_count = 0
            if (len(alice_raw_key)!=0):
                for i in range(len(alice_raw_key)):
                    if (alice_raw_key[i] != bob_raw_key[i]):
                        error_count += 1
                error_rate = error_count / len(alice_raw_key)

            # Display final statistics
            output_widget.insert(tk.END, f"{name1}'s Raw Key: {alice_raw_key}\n")
            output_widget.insert(tk.END, f"{name2}'s Raw Key: {bob_raw_key}\n")
            output_widget.insert(tk.END, f"{name1} measured in the z basis {alice_zcount} times\n")
            output_widget.insert(tk.END, f"{name1} measured in the x basis {alice_xcount} times\n")
            output_widget.insert(tk.END, f"{name2} measured in the z basis {bob_zcount} times\n")
            output_widget.insert(tk.END, f"{name2} measured in the x basis {bob_xcount} times\n")
            output_widget.insert(tk.END, f"QBER: {error_rate}\n")

        # Update status to show successful completion
        status_label.config(text="QKD simulation completed successfully!")
    except Exception as e:
        # Handle any errors that occurred during execution
        status_label.config(text="Error occurred!")
        output_widget.insert(tk.END, f"Error: {str(e)}\n")


def main():
    global root
    # Create the main window
    root = tk.Tk()
    root.title("QKD Program")
    root.geometry("600x600")
    root.config(bg="#1e1e2f")  # Dark background

    # Title Label
    title_label = tk.Label(
        root, text="Quantum Key Distribution Simulator", font=("Helvetica", 16, "bold"), fg="#ffffff", bg="#1e1e2f"
    )
    title_label.pack(pady=10)

    # Input Frame
    input_frame = tk.Frame(root, bg="#2b2b3d")
    input_frame.pack(pady=10, padx=10, fill=tk.X)

    def create_labeled_entry(parent, label_text, row):
        tk.Label(parent, text=label_text, fg="#ffffff", bg="#2b2b3d").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        entry = tk.Entry(parent, width=30)
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    name1_entry = create_labeled_entry(input_frame, "Name 1 :", 0)
    name2_entry = create_labeled_entry(input_frame, "Name 2 :", 1)
    noise_entry = create_labeled_entry(input_frame, "Noise (0 to 1):", 2)
    iterations_entry = create_labeled_entry(input_frame, "Iterations:", 3)
    epr_entry = create_labeled_entry(input_frame, "Number of EPR Pairs:", 4)
    

    # Output Frame
    output_label = tk.Label(root, text="Output:", font=("Helvetica", 12, "bold"), fg="#ffffff", bg="#1e1e2f")
    output_label.pack(pady=5)

    output_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=30, bg="#1e1e2f", fg="#00ff00")
    output_widget.pack(padx=10, pady=5)

    # Progress Bar
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=10)

    # Status Label
    status_label = tk.Label(root, text="", font=("Helvetica", 10), fg="#ffffff", bg="#1e1e2f")
    status_label.pack()

    # Run Button
    def on_run_button_click():
        # Retrieve input values
        name1 = name1_entry.get()
        name2 = name2_entry.get()
        noise = noise_entry.get()
        iterations = iterations_entry.get()
        num_epr = epr_entry.get()
        
        # Input validation
        try:
            noise = float(noise)
            if not (0 <= noise <= 1):
                raise ValueError("Noise must be between 0 and 1.")
        except ValueError as e:
            output_widget.insert(tk.END, f"Invalid Noise value: {e}\n")
            status_label.config(text="Error: Invalid Noise value", fg="red")
            return

        try:
            iterations = int(iterations)
            if iterations <= 0:
                raise ValueError("Iterations must be greater than 0.")
        except ValueError as e:
            output_widget.insert(tk.END, f"Invalid Iterations value: {e}\n")
            status_label.config(text="Error: Invalid Iterations value", fg="red")
            return

        try:
            num_epr = int(num_epr)
            if num_epr <= 3:
                raise ValueError("Number of EPR pairs must be greater than 3.")
        except ValueError as e:
            output_widget.insert(tk.END, f"Invalid Number of EPR pairs value: {e}\n")
            status_label.config(text="Error: Invalid EPR pairs value", fg="red")
            return

        # If all inputs are valid, run the program
        status_label.config(text="Running simulation...", fg="green")
        run_program(name1, name2, noise, iterations, output_widget, progress_bar, status_label, num_epr)


    run_button = ttk.Button(root, text="Run QKD Simulation", command=on_run_button_click)
    run_button.pack(pady=10)

    # Start the Tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    main()