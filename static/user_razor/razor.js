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

	const addAddressButton = document.getElementById("addCheckoutAddress");
	const addressForm = document.getElementById("checkoutAddressForm");
	const addressSelect = document.getElementById("checkoutAddress");
	const addressError = document.getElementById("checkoutAddressError");
	const csrfToken = getCookie("csrftoken");

	const readJsonResponse = async (response) => {
		const contentType = response.headers.get("content-type") || "";
		if (!contentType.includes("application/json")) {
			throw new Error("The server returned an unexpected response. Please try again.");
		}
		return response.json();
	};

	addAddressButton?.addEventListener("click", () => {
		addressForm.classList.toggle("d-none");
		if (!addressForm.classList.contains("d-none")) {
			addressForm.querySelector("input")?.focus();
		}
	});

	addressForm?.addEventListener("submit", async (event) => {
		event.preventDefault();
		addressError.textContent = "";
		const saveButton = addressForm.querySelector("button[type='submit']");
		saveButton.disabled = true;
		try {
			const response = await fetch(addressForm.dataset.addUrl, {
				method: "POST",
				headers: { "X-CSRFToken": csrfToken },
				credentials: "same-origin",
				body: new FormData(addressForm),
			});
			const result = await readJsonResponse(response);
			if (!response.ok || !result.success) {
				throw new Error(Object.values(result.errors || {})[0] || result.message || "Unable to save address.");
			}
			const option = new Option(`${result.address.label} · ${result.address.summary}`, result.address.id, true, true);
			addressSelect.add(option);
			addressForm.reset();
			addressForm.classList.add("d-none");
		} catch (error) {
			addressError.textContent = error.message;
		} finally {
			saveButton.disabled = false;
		}
	});

	checkoutButton.addEventListener("click", async () => {
		const store = document.getElementById("checkoutStore");
		const address = document.getElementById("checkoutAddress");
		const pickupDate = document.getElementById("pickupDate");

		if (!store.value || !address.value || !pickupDate.value) {
			alert("Choose a store, pickup address, and pickup date before continuing.");
			return;
		}

		checkoutButton.disabled = true;
		checkoutButton.textContent = "Opening checkout...";

		try {
			const response = await fetch(checkoutButton.dataset.createUrl, {
				method: "POST",
				headers: {
					"X-CSRFToken": csrfToken,
					"Content-Type": "application/json",
				},
				credentials: "same-origin",
				body: JSON.stringify({
					store_id: store.value,
					address_id: address.value,
					pickup_date: pickupDate.value,
				}),
			});
			const data = await readJsonResponse(response);

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
						const result = await readJsonResponse(verifyResponse);

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
