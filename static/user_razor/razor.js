document.addEventListener("DOMContentLoaded", () => {
	const checkoutButton = document.getElementById("razorpayCheckout");

	if (!checkoutButton) {
		return;
	}

	const getCookie = (name) => {
		const cookie = document.cookie
			.split(";")
			.map((value) => value.trim())
			.find((value) => value.startsWith(`${name}=`));

		return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
	};

	const resetButton = () => {
		checkoutButton.disabled = false;
		checkoutButton.textContent = "Proceed to checkout";
	};

	checkoutButton.addEventListener("click", async () => {
		checkoutButton.disabled = true;
		checkoutButton.textContent = "Opening checkout...";

		try {
			const csrfToken = getCookie("csrftoken");
			const response = await fetch(checkoutButton.dataset.createUrl, {
				method: "POST",
				headers: {
					"X-CSRFToken": csrfToken,
					"Content-Type": "application/json",
				},
				credentials: "same-origin",
			});
			const data = await response.json();

			if (!response.ok || !data.success) {
				throw new Error(data.message || "Unable to start checkout.");
			}

			const razorpay = new Razorpay({
				key: data.key,
				amount: data.amount,
				currency: data.currency,
				name: data.name,
				order_id: data.razorpay_order_id,
				prefill: data.prefill,
				handler: async (payment) => {
					try {
						const verifyResponse = await fetch(checkoutButton.dataset.verifyUrl, {
							method: "POST",
							headers: {
								"X-CSRFToken": csrfToken,
								"Content-Type": "application/json",
							},
							credentials: "same-origin",
							body: JSON.stringify({ ...payment, order_id: data.order_id }),
						});
						const result = await verifyResponse.json();

						if (!verifyResponse.ok || !result.success) {
							throw new Error(result.message || "Payment verification failed.");
						}

						window.location.href = result.redirect_url;
					} catch (error) {
						alert(error.message);
						resetButton();
					}
				},
			});

			razorpay.on("payment.failed", (failure) => {
				alert(failure.error.description || "Payment failed.");
				resetButton();
			});
			razorpay.open();
		} catch (error) {
			alert(error.message);
			resetButton();
		}
	});
});
