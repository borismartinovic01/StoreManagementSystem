pragma solidity ^0.8.18;

contract Order {
    
    address payable owner;
    address payable courier;
    address customer;

    uint transferComplete; //0 - false; 1 - true
    uint pickedUp; //0 - false; 1 - true

    modifier not_after_transfer {
        require ( transferComplete == 0, "Transfer already complete." );
        _;
    }

    modifier not_before_transfer {
        require ( transferComplete == 1, "Transfer not complete." );
        _;
    }

    modifier not_customer{
        require(msg.sender == customer, "Invalid customer account.");
        _;
    }

    modifier not_before_pickedup{
        require(pickedUp == 1, "Delivery not complete.");
        _;
    }

    constructor(address _customer) {
        owner = payable(msg.sender);
        customer = _customer;
        transferComplete = 0;
        pickedUp = 0;
    }

    function pay() external payable not_after_transfer not_customer{
        transferComplete = 1;
    }

    function pick_up_order(address payable _courier) external payable not_before_transfer{
        courier = _courier;
        pickedUp = 1;
    }

    function delivered () external not_customer not_before_transfer not_before_pickedup{
        
        uint amount = address(this).balance;
        owner.transfer(amount / 100 * 80);
        courier.transfer(amount / 100 * 20);
    }

}