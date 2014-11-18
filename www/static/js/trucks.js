/**
 * @jsx React.DOM
 */
var Truck = React.createClass({
  render: function() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.location}</td>
        <td>{this.props.status}</td>
      </tr>
    );
  }
});

var TruckTable = React.createClass({
  loadStatusFromServer: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadStatusFromServer();
    setInterval(this.loadStatusFromServer, this.props.pollInterval);
  },
  render: function() {
    var truckNodes = this.state.data.map(function(truck, index) {
      return (
        <Truck name={truck.name} location={truck.location} status={truck.status} key={index} />
      );
    });
    return (
      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th className="col-md-3">Truck Name</th>
              <th className="col-md-3">Location</th>
              <th className="col-md-3">Value</th>
            </tr>
          </thead>
          <tbody>
            {truckNodes}
          </tbody>
        </table>
      </div>
    );
  }
});

React.renderComponent(
  <TruckTable url="trucks.json" pollInterval={1000} />,
  document.getElementById('trucks')
);
